import csv,re
from pathlib import Path
mapping=[
('FR-01','register/create_user','users,portfolios,wallets,wallet_ledger','test_registration_credit_once; test_registration_then_immediate_login_commit'),
('FR-02','login/current/role/logout','users,auth_sessions','test_owner_and_csrf_and_logout; test_role_boundaries'),
('FR-03','add_stock/edit_stock','stocks','test_catalog_and_disabled_stock'),
('FR-04','stocks/history','stocks,price_ticks','test_catalog_and_disabled_stock; browser-smoke.mjs'),
('FR-05','tick/change_session','price_ticks,market_sessions','test_immediate_limit_and_reopen; browser-demo.mjs'),
('FR-06','create_user','portfolios,wallets,wallet_ledger','test_registration_credit_once'),
('FR-07','wallet/ledger','wallets,wallet_ledger','test_canonical_demo; test_rejections_and_cancel'),
('FR-08','trading.place/settle','orders,trades,wallets,holdings','test_canonical_demo'),
('FR-09','trading.place','orders,wallets,holdings','test_rejections_and_cancel; test_sell_reservations_and_duplicate_tick'),
('FR-10','trading.process_pending','price_ticks,orders,trades','test_canonical_demo; test_sell_reservations_and_duplicate_tick'),
('FR-11','trading.cancel','orders,wallets,holdings','test_rejections_and_cancel; test_cancel_fill_race'),
('FR-12','trading.place; OrderInput','orders,notifications','test_stale_and_validation; test_rejections_and_cancel; test_catalog_and_disabled_stock'),
('FR-13','trading.settle; trades','trades','test_canonical_demo; browser-demo.mjs'),
('FR-14','trading.settle; db_session','wallets,wallet_ledger,holdings,orders,trades,audit_logs,notifications','test_forced_rollback'),
('FR-15','portfolio; trading.average_cost','holdings,wallets,price_ticks','test_canonical_demo; test_cost_formula'),
('FR-16','records/orders/trades','orders,trades,stocks','test_watchlist_notifications_admin; browser-demo.mjs'),
('FR-17','watchlists/new_watchlist/watch_item','watchlists,watchlist_items','test_watchlist_notifications_admin'),
('FR-18','portfolio; UI overview','wallets,holdings,price_ticks','test_canonical_demo; browser-demo.mjs'),
('FR-19','notify/notifications/read_notification','notifications','test_watchlist_notifications_admin; test_rejections_and_cancel'),
('FR-20','trading.record; audit','audit_logs','test_watchlist_notifications_admin; browser-demo.mjs'),
('FR-21','users/summary/audit','users,orders,trades,stocks,audit_logs','test_watchlist_notifications_admin; test_role_boundaries'),
('FR-22','trading.place; tick','orders,trades,price_ticks','test_concurrent_duplicate_and_payload_conflict; test_sell_reservations_and_duplicate_tick')]
with Path('docs/traceability.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['requirement','implemented_functions','tables','verification','evidence']);
 for ident,fn,tables,test in mapping:w.writerow([ident,fn,tables,test,'evidence/pytest.xml; evidence/browser-demo.json; source code'])
with Path('docs/placeholder_register.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['id','source','status','resolution_or_authority','date'])
 for name in ['idea.md','technical.md','implementation.md','flowcharts.md']:
  p=Path('docs')/name;s=p.read_text(encoding='utf-8-sig')
  ids=sorted(set(re.findall(r'(?:OPEN-\d+|[A-Z]+-TBD-\d+)',s)))
  for ident in ids:
   if ident.startswith('OPEN-'):status='RESOLVED_OR_STUDENT_OWNED';ref='decision_log.md: individual OPEN entries'
   elif ident.startswith(('DIAG-','LAB-','PLAN-')):status='SOURCE_MATERIAL_DELIVERED';ref='lab-source-guide.md; student authors experiment diagrams/schedule/reviews per user instruction'
   else:status='RESOLVED_BY_IMPLEMENTATION';ref='decision_log.md; as-built.md; schema.md; openapi.json; evidence/'
   w.writerow([ident,name,status,ref,'2026-11-16'])
  amendment='> **Implementation amendment (2026-11-16):** This file is the original planning baseline, preserved for context. The implemented contract is documented in [decision_log.md](decision_log.md), [as-built.md](as-built.md), [schema.md](schema.md), [openapi.json](openapi.json) and [traceability.csv](traceability.csv). Historical placeholders are reconciled in [placeholder_register.csv](placeholder_register.csv). The user explicitly excluded authoring experiment submissions: [lab-source-guide.md](lab-source-guide.md) supplies material for all 13. No Docker, deployment, student identities or invented sign-offs.\n\n'
  if not s.startswith('> **Implementation amendment'):p.write_text(amendment+s,encoding='utf-8')
