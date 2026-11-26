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
 _ = json.NewEncoder(os.Stdout).Encode(map[string]any{"status":"parsed","package":file.Name.Name,"symbols":symbols,"imports":imports,"parser":"go-syntax"})
}
