package verification

import "testing"

func TestRegistry(cur realm, t *testing.T) {
    if Count() != 0 {
        t.Fatal("expected empty registry")
    }
    hash := "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    if Render(hash) != "# RealmProof Evidence Registry\n\nEvidence digest not found.\n" {
        t.Fatal("expected digest lookup to report missing")
    }
    index := RegisterEvidence(cross(cur), hash)
    if index != 1 || Count() != 1 || !HasEvidence(hash) {
        t.Fatal("failed to register evidence")
    }
    if Render(hash) != "# RealmProof Evidence Registry\n\nRegistered evidence digest: `" + hash + "`\n" {
        t.Fatal("expected digest lookup to report the stored hash")
    }
}
