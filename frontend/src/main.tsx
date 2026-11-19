import { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, ChevronRight, Database, FlaskConical, History as HistoryIcon, Layers3, LayoutDashboard, Menu, Monitor, ScanSearch, ChartNoAxesCombined, X } from 'lucide-react'
import type { Config, Overview as OverviewData } from './api'
import { modeName, sourceName, useResource } from './api'
import { Overview } from './Overview'
import { Ask, Investigate } from './Analysis'
import { DataPage, EvalPage, History } from './Library'
import './style.css'

const nav = [
  { id: 'overview', title: '运营概览', icon: LayoutDashboard }, { id: 'ask', title: '分析工作台', icon: ChartNoAxesCombined },
  { id: 'investigation', title: '差评调查', icon: ScanSearch }, { id: 'data', title: '数据与指标', icon: Layers3 },
  { id: 'evaluation', title: '评估记录', icon: FlaskConical }, { id: 'history', title: '运行历史', icon: HistoryIcon },
]
function current() { return nav.find(n => n.id === window.location.hash.slice(1))?.id || 'overview' }
function App() {
  const [page, setPage] = useState(current)
  const [menu, setMenu] = useState(false)
  const [configOpen, setConfigOpen] = useState(false)
  const main = useRef<HTMLElement>(null)
  const menuButton = useRef<HTMLButtonElement>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  const sidebar = useRef<HTMLElement>(null)
  const overview = useResource<OverviewData>('overview'), config = useResource<Config>('config/status')
  const title = nav.find(n => n.id === page)!.title
  useEffect(() => {
    function change() { setPage(current()); setMenu(false); window.scrollTo(0,0); requestAnimationFrame(() => main.current?.focus({preventScroll: true})) }
    window.addEventListener('hashchange', change)
    return () => window.removeEventListener('hashchange', change)
  }, [])
  useEffect(() => { document.title = title + ' · Commerce Lens' }, [title])
  useEffect(() => {
    if (!menu) return
    const links = Array.from(sidebar.current?.querySelectorAll<HTMLElement>('a,button') || [])
    sidebar.current?.querySelector<HTMLElement>('[aria-current]')?.focus()
    function keydown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setMenu(false)
        requestAnimationFrame(() => menuButton.current?.focus())
      }
      if (e.key !== 'Tab') return
      if (e.shiftKey && document.activeElement === links[0]) { e.preventDefault(); links.at(-1)?.focus() }
      if (!e.shiftKey && document.activeElement === links.at(-1)) { e.preventDefault(); links[0]?.focus() }
    }
    const desktop = window.matchMedia('(min-width: 951px)')
    const onDesktop = () => { if (desktop.matches) setMenu(false) }
    desktop.addEventListener('change', onDesktop)
    document.addEventListener('keydown', keydown)
    return () => { desktop.removeEventListener('change', onDesktop); document.removeEventListener('keydown', keydown) }
  }, [menu])
  useEffect(() => { if (configOpen) dialog.current?.showModal(); else dialog.current?.close() }, [configOpen])
  return <div className="app"><a className="skip" href="#main" onClick={e => {e.preventDefault(); main.current?.focus()}}>跳到主内容</a>
    <aside id="sidebar" ref={sidebar} role={menu ? "dialog" : undefined} aria-label="工作空间导航" aria-modal={menu || undefined} className={'sidebar' + (menu ? ' open' : '')}>
      <button className="drawer-close" aria-label="关闭导航菜单" onClick={() => {setMenu(false); requestAnimationFrame(() => menuButton.current?.focus())}}><X size={19}/></button>
      <a href="#overview" className="brand" onClick={() => setMenu(false)}><img src="/lens.svg" alt="" width="39" height="39"/><span>Commerce Lens<small>电商运营工作台</small></span></a>
      <nav aria-label="主导航">{['工作区','管理'].map((group, i) => <div className="nav-group" key={group}><div className="nav-label">{group}</div>
        {nav.slice(i ? 4 : 0, i ? 6 : 4).map(item => <a key={item.id} href={'#' + item.id} aria-current={page === item.id ? 'page' : undefined} onClick={() => {setMenu(false); if (item.id === page) requestAnimationFrame(() => main.current?.focus())}}><item.icon size={19}/>{item.title}</a>)}</div>)}</nav>
      <div className="sidebar-bottom"><span className="device"><Monitor size={18}/></span><div><strong>本地工作空间</strong><small>单用户模式</small></div></div>
    </aside>
    <div className="workspace" inert={menu}><header className="top-bar"><div className="crumb"><button className="menu-button" aria-label="切换导航" aria-expanded={menu} aria-controls="sidebar" ref={menuButton} onClick={() => setMenu(!menu)}>{menu ? <X size={20}/> : <Menu size={20}/>}</button><span className="crumb-root">工作空间</span><ChevronRight className="crumb-sep" size={14}/><strong>{title}</strong></div>
      <div className="top-info"><span className="top-source"><Database size={14}/>{sourceName(overview.data?.source)}</span><button className="config-button" onClick={() => setConfigOpen(true)} aria-label="查看模式与模型配置"><span className={'dot ' + (config.error ? 'unknown' : '')}/>{config.error ? '配置状态未知' : modeName(config.data?.mode)}</button></div>
    </header>
    <main id="main" ref={main} tabIndex={-1} className="main" key={page}>
      {page === 'overview' ? <Overview {...overview}/> : page === 'ask' ? <Ask config={config.data}/> : page === 'investigation' ? <Investigate/> : page === 'data' ? <DataPage/> : page === 'evaluation' ? <EvalPage config={config.data}/> : <History/>}
    </main></div>
    {menu && <button className="scrim" tabIndex={-1} aria-label="关闭导航" onClick={() => {setMenu(false); requestAnimationFrame(() => menuButton.current?.focus())}}/>}
    <dialog aria-labelledby="config-title" ref={dialog} onCancel={() => setConfigOpen(false)} onClose={() => setConfigOpen(false)}><div className="panel-head"><div className="symbol-heading"><span className="icon-tile blue"><Activity size={19}/></span><h2 id="config-title">模式与模型配置</h2></div><button className="icon-button" aria-label="关闭配置状态" onClick={() => setConfigOpen(false)}><X size={18}/></button></div>
      {config.error ? <p>{config.error}</p> : !config.data ? <p>正在读取配置…</p> : <><dl className="facts"><div><dt>当前模式</dt><dd>{modeName(config.data.mode)}</dd></div><div><dt>模型配置</dt><dd>{config.data.configured ? '已配置' : '尚未配置'}</dd></div>{config.data.configured && <div><dt>模型名称</dt><dd>{config.data.model || '—'}</dd></div>}</dl>
      {!config.data.configured && <p className="body-copy">离线演示支持预设分析问题。要启用模型，请按 README 在本地环境文件中设置模型服务地址、名称与密钥，然后重启服务。</p>}</>}
    </dialog>
  </div>
}
createRoot(document.getElementById('root')!).render(<App/>)
