import { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, ChevronRight, Database, FlaskConical, History as HistoryIcon, LayoutDashboard, Menu, Monitor, ChartNoAxesCombined, X } from 'lucide-react'
import type { Config, Overview as OverviewData } from './api'
import { modeName, sourceName, useResource } from './api'
import { Overview } from './Overview'
import { Ask } from './Ask'
import { EvalPage, History } from './Library'
import './style.css'

const nav = [
  { id: 'overview', title: 'Operations overview', icon: LayoutDashboard }, { id: 'ask', title: 'Ask the agent', icon: ChartNoAxesCombined },
  { id: 'evaluation', title: 'Evaluation', icon: FlaskConical }, { id: 'history', title: 'Run history', icon: HistoryIcon },
]
function current() {
  let route = window.location.hash.slice(1)
  if (route === 'investigation' || route === 'data') {
    route = route === 'data' ? 'ask/data' : 'ask/delivery'
    window.history.replaceState(window.history.state, '', '#' + route)
  }
  if (route === 'ask/data' || route === 'ask/delivery') return route
  return nav.some(n => n.id === route) ? route : 'overview'
}
function App() {
  const [route, setRoute] = useState(current)
  const [page, tool] = route.split('/')
  const [menu, setMenu] = useState(false)
  const [configOpen, setConfigOpen] = useState(false)
  const main = useRef<HTMLElement>(null)
  const menuButton = useRef<HTMLButtonElement>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  const sidebar = useRef<HTMLElement>(null)
  const overview = useResource<OverviewData>('overview'), config = useResource<Config>('config/status')
  const title = nav.find(n => n.id === page)!.title
  useEffect(() => {
    function change() { setRoute(current()); setMenu(false); window.scrollTo(0,0); requestAnimationFrame(() => main.current?.focus({preventScroll: true})) }
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
  return <div className="app"><a className="skip" href="#main" onClick={e => {e.preventDefault(); main.current?.focus()}}>Skip to main content</a>
    <aside id="sidebar" ref={sidebar} role={menu ? "dialog" : undefined} aria-label="Workspace navigation" aria-modal={menu || undefined} className={'sidebar' + (menu ? ' open' : '')}>
      <button className="drawer-close" aria-label="Close navigation menu" onClick={() => {setMenu(false); requestAnimationFrame(() => menuButton.current?.focus())}}><X size={19}/></button>
      <a href="#overview" className="brand" onClick={() => setMenu(false)}><img src="/lens.svg" alt="" width="39" height="39"/><span>Commerce Lens<small>E-commerce Operations Agent</small></span></a>
      <nav aria-label="Main navigation">{['Workspace','Records'].map((group, i) => <div className="nav-group" key={group}><div className="nav-label">{group}</div>
        {(i ? nav.slice(2) : nav.slice(0, 2)).map(item => <a key={item.id} href={'#' + item.id} aria-current={page === item.id ? 'page' : undefined} onClick={() => {setMenu(false); if (item.id === page) requestAnimationFrame(() => main.current?.focus())}}><item.icon size={19}/>{item.title}</a>)}</div>)}</nav>
      <div className="sidebar-bottom"><span className="device"><Monitor size={18}/></span><div><strong>Local workspace</strong><small>Single-user mode</small></div></div>
    </aside>
    <div className="workspace" inert={menu}><header className="top-bar"><div className="crumb"><button className="menu-button" aria-label="Toggle navigation" aria-expanded={menu} aria-controls="sidebar" ref={menuButton} onClick={() => setMenu(!menu)}>{menu ? <X size={20}/> : <Menu size={20}/>}</button><span className="crumb-root">Workspace</span><ChevronRight className="crumb-sep" size={14}/><strong>{title}</strong></div>
      <div className="top-info"><span className="top-source"><Database size={14}/>{sourceName(overview.data?.source)}</span><button className="config-button" onClick={() => setConfigOpen(true)} aria-label="View mode and model settings"><span className={'dot ' + (config.error ? 'unknown' : '')}/>{config.error ? 'Mode unavailable' : modeName(config.data?.mode)}</button></div>
    </header>
    <main id="main" ref={main} tabIndex={-1} className="main" key={page}>
      {page === 'overview' ? <Overview {...overview}/> : page === 'ask' ? <Ask config={config.data} tool={tool}/> : page === 'evaluation' ? <EvalPage config={config.data}/> : <History/>}
    </main></div>
    {menu && <button className="scrim" tabIndex={-1} aria-label="Close navigation" onClick={() => {setMenu(false); requestAnimationFrame(() => menuButton.current?.focus())}}/>}
    <dialog aria-labelledby="config-title" ref={dialog} onCancel={() => setConfigOpen(false)} onClose={() => setConfigOpen(false)}><div className="panel-head"><div className="symbol-heading"><span className="icon-tile blue"><Activity size={19}/></span><h2 id="config-title">Mode and model settings</h2></div><button className="icon-button" aria-label="Close settings" onClick={() => setConfigOpen(false)}><X size={18}/></button></div>
      {config.error ? <p>{config.error}</p> : !config.data ? <p>Loading settings…</p> : <><dl className="facts"><div><dt>Current mode</dt><dd>{modeName(config.data.mode)}</dd></div><div><dt>Model setup</dt><dd>{config.data.configured ? 'Configured' : 'Not configured'}</dd></div>{config.data.configured && <div><dt>Model name</dt><dd>{config.data.model || '—'}</dd></div>}</dl>
      {!config.data.configured && <p className="body-copy">Offline mode supports the example questions and all analysis skills. To enable a model, follow the README to set the endpoint, model name, and API key in the local environment file, then restart the service.</p>}</>}
    </dialog>
  </div>
}
createRoot(document.getElementById('root')!).render(<App/>)
