from pathlib import Path

p = Path("frontend/src/main.tsx")
s = p.read_text(encoding="utf-8-sig")
s = s.replace(
    "csrf=d.csrf;setUser(d.user)}).catch",
    "csrf=d.csrf;setUser(d.user);setPage(d.user.role==='ADMIN'?'Administration':d.user.role==='MARKET_OPERATOR'?'Market operations':'Overview')}).catch",
)
s = s.replace(
    "{themeButton}</div></header>",
    "{themeButton}<button className=\"icon-button mobile-logout\" aria-label=\"Sign out\" onClick={()=>act(async()=>{await api('/auth/logout','POST');setUser(null);setData({});setSelected(0)},'Signed out')}><LogOut size={17}/></button></div></header>",
)
p.write_text(s, encoding="utf-8")
