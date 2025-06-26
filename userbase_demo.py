import userbase

for name, password in ("otto", "geheim"), ("ina", "34567"):
    print( f"Nutzer {name} konnte {'' if userbase.authenticate(name, password) else 'nicht ' }angemeldet werden")