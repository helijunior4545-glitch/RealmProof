package ledger
var available int
var held int
var paid int
var frozen bool
func Balance() int { return available }
func Held() int { return held }
func Paid() int { return paid }
func Freeze(value bool) bool { frozen = value; return true }
func Deposit(amount int) bool {
    if frozen || amount <= 0 || amount > 1000000000-available-held-paid { return false }
    available += amount
    return true
}
func Reserve(amount int, authorized bool) bool {
    if frozen || !authorized || amount <= 0 || amount > available { return false }
    available -= amount
    held += amount
    return true
}
func Release(amount int, authorized bool) bool {
    if frozen || !authorized || amount <= 0 || amount > held { return false }
    held -= amount
    available += amount
    return true
}
func Settle(amount int, authorized bool) bool {
    if frozen || !authorized || amount <= 0 || amount > held { return false }
    held -= amount
    paid += amount
    return true
}
