// Parse source as data; never compile or execute input.
package main

import (
 "bytes"
 "encoding/json"
 "go/ast"
 "go/format"
 "go/parser"
 "go/token"
 "io"
 "os"
)

type Symbol struct {
 Kind string `json:"kind"`
 Name string `json:"name"`
 Public bool `json:"public"`
 Line int `json:"line"`
 Signature string `json:"signature"`
}
type Indicator struct {
 Rule string `json:"rule"`
 Function string `json:"function"`
 Line int `json:"line"`
 Reason string `json:"reason"`
}
type Call struct {
 Caller string `json:"caller"`
 CallerLine int `json:"caller_line"`
 Target string `json:"target"`
 Line int `json:"line"`
 Kind string `json:"kind"`
}
func render(f *token.FileSet, n ast.Node) string {
 var b bytes.Buffer
 if n != nil { _ = format.Node(&b, f, n) }
 return b.String()
}
func main() {
 data, err := io.ReadAll(io.LimitReader(os.Stdin, 1048577))
 if err != nil || len(data)>1048576 { os.Exit(2) }
 fs := token.NewFileSet()
 file, err := parser.ParseFile(fs, "source.gno", data, parser.SkipObjectResolution)
 if err != nil {
  _ = json.NewEncoder(os.Stdout).Encode(map[string]any{"status":"syntax_error"})
  return
 }
 symbols := []Symbol{}
 calls := []Call{}
 indicators := []Indicator{}
 indicatorsTruncated := false
 addIndicator := func(rule, function string, pos token.Pos, reason string) {
  if len(indicators)>=500 { indicatorsTruncated=true; return }
  indicators=append(indicators,Indicator{rule,function,fs.Position(pos).Line,reason})
 }
 truncated := false
 add := func(kind string, name *ast.Ident, sig string) {
  symbols = append(symbols, Symbol{kind,name.Name,name.IsExported(),fs.Position(name.Pos()).Line,sig})
 }
 for _, d := range file.Decls {
  switch v := d.(type) {
  case *ast.FuncDecl:
   kind := "function"
   sig := render(fs,v.Type)
   if v.Recv != nil { kind = "method"; sig = render(fs,v.Recv)+" "+sig }
   add(kind,v.Name,sig)
   if v.Body != nil {
    ast.Inspect(v.Body, func(n ast.Node) bool {
     if _, ok := n.(*ast.FuncLit); ok { return false }
     switch node := n.(type) {
     case *ast.BinaryExpr:
      switch node.Op {
      case token.QUO, token.REM: addIndicator("divisor_boundary",v.Name.Name,node.OpPos,"Review zero divisors and boundary inputs.")
      case token.ADD, token.SUB, token.MUL: addIndicator("arithmetic_boundary",v.Name.Name,node.OpPos,"Review numeric limits and arithmetic invariants.")
      }
     case *ast.AssignStmt:
      switch node.Tok {
      case token.ADD_ASSIGN, token.SUB_ASSIGN, token.MUL_ASSIGN, token.QUO_ASSIGN, token.REM_ASSIGN:
       addIndicator("compound_update",v.Name.Name,node.TokPos,"Review mutation and numeric boundaries; storage scope is unresolved.")
      }
     case *ast.IndexExpr:
      addIndicator("index_boundary",v.Name.Name,node.Lbrack,"Review index bounds or missing map keys; operand type is unresolved.")
     case *ast.CallExpr:
      if ident, ok := node.Fun.(*ast.Ident); ok && ident.Name=="panic" {
       addIndicator("panic_candidate",v.Name.Name,node.Pos(),"Review failure paths; the identifier may be shadowed.")
      }
     }
     c, ok := n.(*ast.CallExpr)
     if !ok { return true }
     if len(calls) >= 2000 { truncated = true; return true }
     target, classification := "", "expression"
     switch fn := c.Fun.(type) {
     case *ast.Ident: target, classification = fn.Name, "identifier"
     case *ast.SelectorExpr: target, classification = render(fs,fn), "selector"
     default: target = render(fs,c.Fun)
     }
     if len(target)>512 { target = "[complex expression]" }
     calls = append(calls,Call{v.Name.Name,fs.Position(v.Name.Pos()).Line,target,fs.Position(c.Pos()).Line,classification})
     return true
    })
   }
  case *ast.GenDecl:
   for _, s := range v.Specs {
    switch n := s.(type) {
    case *ast.TypeSpec: add("type",n.Name,render(fs,n.Type))
    case *ast.ValueSpec:
     for _, name := range n.Names { add(v.Tok.String(),name,render(fs,n.Type)) }
    }
   }
  }
 }
 imports := []string{}
 for _, i := range file.Imports { imports = append(imports,i.Path.Value) }
 _ = json.NewEncoder(os.Stdout).Encode(map[string]any{"status":"parsed","package":file.Name.Name,"symbols":symbols,"imports":imports,"parser":"go-syntax","calls":calls,"calls_truncated":truncated,"indicators":indicators,"indicators_truncated":indicatorsTruncated})
}
