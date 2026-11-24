package transfer

// Transfer is a deterministic demo contract function, not a live token transfer.
func Transfer(balance int, amount int, authorized bool) (string, int) {
    if !authorized || amount <= 0 || amount > balance {
        return "rejected", balance
    }
    return "success", balance - amount
}
