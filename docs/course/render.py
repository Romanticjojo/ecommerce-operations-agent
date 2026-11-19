"""Rebuild project-update.pdf after editing project-update.md.

Install the optional authoring tools in a temporary directory, outside the application:

    npm install --prefix /tmp/commerce-pdf-tools markdown-it@14.1.0 mermaid@11.12.2
    uv run --with playwright==1.65.2 playwright install chromium
    uv run --with playwright==1.65.2 python docs/course/render.py /tmp/commerce-pdf-tools

Set PDF_BROWSER_CHANNEL=chrome to use installed Google Chrome.
"""

import argparse
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description='Render the four-page course update')
parser.add_argument('tool_directory', type=Path, help='npm prefix containing markdown-it and mermaid')
args = parser.parse_args()
src = Path(__file__).with_name('project-update.md')
out = src.with_suffix('.pdf')
folder = args.tool_directory.resolve()
pages=src.read_text().split('<!-- page -->')
if len(pages) != 4:
    raise SystemExit('Use three <!-- page --> markers to divide the update into four pages.')
labels = ['Project specification', 'Architecture', 'Verification design', 'Implementation status']
style='''
* { box-sizing:border-box }
@page {size: letter; margin:0}
html, body { margin:0; background:white; }
body {color:#1a2630; font-family:Arial, Helvetica, sans-serif; }
.page {width:8.5in; height:11in; padding:32px 48px 38px; position:relative; break-after:page; }
.page:last-child {break-after:auto}
header {display:flex; justify-content:space-between; text-transform:uppercase; font:700 11px Arial; letter-spacing:1.5px; color:#27565c; border-bottom:2px solid #297e7c; padding-bottom:10px; margin-bottom:19px}
footer {position:absolute; left:48px; right:48px; bottom:23px; color:#526368; padding-top:8px; border-top:1px solid #adc5c5; display:flex; justify-content:space-between; font-size:10px; letter-spacing:0.6px;}
h1 {font: bold 37px/1.05 Georgia,'Times New Roman',serif; letter-spacing:-1px; margin:0 0 13px; color:#143842;}
h2 {font:bold 20px/1.1 Georgia,serif; margin:20px 0 8px; color:#154851;}
h3 {font:bold 15px/1.16 Arial,sans-serif; margin:16px 0 5px; color:#1c4f58;}
p, td, th {font-size:13.4px;line-height:1.38;}
p {margin:7px 0;}
table {border-collapse:collapse; width:100%; margin:7px 0; }
td,th {text-align:left; vertical-align:top; padding:5.5px 8px; border-bottom:1px solid #d5e0e0;}
thead th {background:#e2eded; color:#1c474e; font-size:12px;}
tbody tr:nth-child(even) {background:#f7f9f9;}
a {color:#126567; text-decoration:underline; }
.p1 h1+p {font-size:13px; color:#38656b; font-weight:bold; margin:-4px 0 12px;}
.p1 table:first-of-type td:first-child, .p4 td:first-child {white-space:nowrap;}
.p1 table:first-of-type td:last-child {width:106px;font-size:12px;}
.p1 td,.p1 th {padding-top:4px;padding-bottom:4px;}
.p1 h2{margin-top:14px;}
.p1 table:nth-of-type(2) td:first-child {width:172px;}
.p2 h1 {margin-bottom:16px}
.p2 h2 {font-size:19px; margin:13px 0 3px;}
.diagram {width:100%; display:flex; align-items:center; justify-content:center; padding:3px 5px; border-bottom:1px solid #dce7e7; }
.diagram svg{height:100%;max-width:100% !important;}
.d0 {height:141px;} .d1 {height:248px;} .d2 {height:181px;}
.p2 p {margin:6px 0 14px; font-size:13.1px;}
.p3 h2 {border-bottom:1px solid #a6bfbf; padding-bottom:5px;}
.p3 h3 {margin-top:15px;}
.p3 p strong{font-size:12px;color:#25565e;}
.p3 p {margin-top:4px;}
.p4 td:first-child {width:114px;}
.p4 table:first-of-type td:first-child {white-space:normal; width:300px;}
.p4 h2 {margin-top:15px;}
.p4 p:last-child {font-size:11.4px;margin-top:15px;}
'''
with sync_playwright() as p:
    b=p.chromium.launch(channel=os.getenv('PDF_BROWSER_CHANNEL'), headless=True)
    page=b.new_page(viewport={'width':816,'height':1056},device_scale_factor=1)
    page.set_content('<!doctype html><html lang="en"><head><title>E-commerce Operations Agent | DSC 200 Project Update</title><style>'+style+'</style></head><body></body></html>')
    page.add_script_tag(path=str(folder/'node_modules/markdown-it/dist/markdown-it.min.js'))
    page.add_script_tag(path=str(folder/'node_modules/mermaid/dist/mermaid.min.js'))
    page.evaluate('''async ({pages, labels})=>{
       const md=window.markdownit({html:false}); const diagrams = [];
       md.renderer.rules.fence=(tokens,idx)=>{const token=tokens[idx];const id=diagrams.length;diagrams.push(token.content);return '<div class="diagram d'+id+'"></div>'};
       pages.forEach((text,i)=>{const s=document.createElement('section');s.className='page p'+(i+1);s.innerHTML='<header><span>Commerce Lens</span><span>'+labels[i]+'</span></header><main>'+md.render(text)+'</main><footer><span>DSC 200 · Fall 2026</span><span>'+String(i+1).padStart(2,'0')+' / 04</span></footer>';document.body.appendChild(s);});
       mermaid.initialize({startOnLoad:false,securityLevel:'strict', theme:'base',
         fontFamily:'Arial, sans-serif',
         themeVariables:{primaryColor:'#e8f1f1',primaryTextColor:'#183e45',primaryBorderColor:'#649392',lineColor:'#426e72',tertiaryColor:'#f4f8f8',actorBkg:'#e8f1f1',actorTextColor:'#183e45',actorBorder:'#649392',signalTextColor:'#223b41',edgeLabelBackground:'#ffffff',fontSize:'16px'},
         sequence:{mirrorActors:false,actorMargin:15,boxMargin:4,width:90,height:33,messageMargin:19,diagramMarginX:5,diagramMarginY:5,noteMargin:5},
         class:{diagramPadding:4},state:{padding:4}});
       for(const [i,code] of diagrams.entries()){ const {svg}=await mermaid.render('diagram-'+i,code);document.querySelector('.d'+i).innerHTML=svg;}
       await document.fonts.ready;
    }''',{'pages':pages,'labels':labels})
    metrics = page.locator('.page').evaluate_all('''ss=>ss.map(s=>({mainHeight:s.querySelector('main').getBoundingClientRect().height,free:s.querySelector('footer').getBoundingClientRect().top - s.querySelector('main').getBoundingClientRect().bottom}))''')
    for number, layout in enumerate(metrics, 1):
        if layout['free'] < 10:
            raise SystemExit(f'Page {number} exceeds its text area. Shorten the content before rendering.')
    page.emulate_media(media="print")
    page.pdf(path=str(out),prefer_css_page_size=True,print_background=True,tagged=True)
    print(f'Rendered four pages to {out.name}')
    b.close()
