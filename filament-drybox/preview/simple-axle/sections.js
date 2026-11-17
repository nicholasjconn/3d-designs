const colors={frame:'#586368',core:'#318665',disc:'#407bc5',clip:'#ab52ad','left-bearing':'#ed8618','right-bearing':'#ed8618'};
const names={frame:'Frame',core:'Axle/core',disc:'Drive disc',clip:'Printed clip','left-bearing':'608 reference','right-bearing':'608 reference'};
const fmt=x=>Number(x.toFixed(3)),inch=x=>(x/25.4).toFixed(3)+'″';
const path=loop=>'M'+loop.map(([x,v])=>`${x},${-v}`).join('L')+'Z';
const line=(x,v,xx,vv,color='#466253',dash='')=>`<line x1="${x}" y1="${-v}" x2="${xx}" y2="${-vv}" stroke="${color}" stroke-width=".16" stroke-dasharray="${dash}"/>`;
const text=(x,v,s,size=2.8,anchor='middle')=>`<text x="${x}" y="${-v}" font-family="system-ui" font-size="${size}" text-anchor="${anchor}" fill="#233c31">${s}</text>`;
const dimension=(a,b,v,label)=>line(a,v,b,v)+line(a,v-1.1,a,v+1.1)+line(b,v-1.1,b,v+1.1)+text((a+b)/2,v+1.3,label);
function shapes(section){return Object.entries(section.components).map(([name,faces])=>faces.map(f=>`<path d="${f.loops_mm.map(path).join('')}" fill="${colors[name]}" fill-rule="evenodd" stroke="#243f32" stroke-width=".13"><title>${names[name]} · native section area ${fmt(f.native_area_mm2)} mm²</title></path>`+(f.imprint_paths_mm||[]).map(p=>`<path d="M${p.map(([x,v])=>`${x},${-v}`).join('L')}" fill="none" stroke="#243f32" stroke-width=".13"/>`).join('')).join('')).join('')}
function bounds(section){const points=Object.values(section.components).flatMap(faces=>faces.flatMap(f=>f.loops_mm.flat()));if(!points.length)throw Error('Empty native section');return [Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1])),Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))]}
function draw(svg,section,data,detail){
  const d=data.dimensions_mm,p=data.parameters;let [x0,v0,x1,v1]=detail?section.detail_box_mm:bounds(section);if(!detail){x0=Math.min(x0,d.left_wall_x);x1=Math.max(x1,d.right_wall_x)}
  const margin=detail?2:8,above=detail?12:24,below=detail?3:17;
  svg.setAttribute('viewBox',`${x0-margin} ${-(v1+above)} ${x1-x0+2*margin} ${v1-v0+above+below}`);
  svg.setAttribute('aria-label',`${section.label}, ${detail?'enlarged detail':'complete section'}. ${section.description}`);
  const clipId=detail?'detail-crop':'full-crop';
  let html=`<defs><clipPath id="${clipId}"><rect x="${x0}" y="${-v1}" width="${x1-x0}" height="${v1-v0}"/></clipPath></defs>`;
  html+=`<g clip-path="url(#${clipId})">${shapes(section)}</g>`;
  for(const x of [d.left_wall_x,d.right_wall_x])if(x>=x0&&x<=x1)html+=line(x,v0-1,x,v1+3,'#448ac5','1 .6');
  if(detail){
    if(section.id!=='base'){
      html+=text((x0+x1)/2,v1+8,'Detail · dimensions in mm',2.1);
      if(section.id==='shaft'){
        html+=dimension(p.driveFront,d.right_wall_x,v1+1.2,fmt(p.airGap)+' gap');
        html+=line(p.driveFront,v1+1.2,p.driveFront,111,'#448ac5','1 .6');
      }
      if(section.id==='stops'||section.id==='top')html+=text((x0+x1)/2,v1+4,'Wall X = '+fmt(d.right_wall_x),1.8);
    }else html+=text((x0+x1)/2,v1+2,'Smooth future-screw pilot',2.1);
  }else{
    html+=dimension(d.left_wall_x,d.right_wall_x,v1+17,`W1 · ${fmt(d.wall_span)} mm / ${inch(d.wall_span)}`);
    html+=dimension(d.left_wall_x,p.driveFront,v1+9,`P1 · ${fmt(p.driveFront-d.left_wall_x)} mm / ${inch(p.driveFront-d.left_wall_x)}`);
    html+=text(d.left_wall_x,v1+3,'Left wall',2.5)+text(d.right_wall_x,v1+3,'Drive wall',2.5);
    html+=dimension(d.base_x[0],d.base_x[1],v0-8,`B1 · ${fmt(d.base_width)} mm / ${inch(d.base_width)}`);
    for(const x of d.base_x)html+=line(x,v0,x,v0-8);
    const [a,b,c,e]=section.detail_box_mm;html+=`<rect x="${a}" y="${-e}" width="${c-a}" height="${e-b}" fill="none" stroke="#a04480" stroke-width=".25" stroke-dasharray="1 .6"/>`;
    html+=text((x0+x1)/2,v0-13,section.plane==='XY'?'X → across axle · Y ↑ up':'X → across axle · Z ↑ front/back',2.6);
  }
  svg.innerHTML=html;
}
export async function initSections(model){
  const response=await fetch('./bearing-sections.json',{cache:'no-store'});if(!response.ok)throw Error('Sections HTTP '+response.status);const data=await response.json();if(data.schema!=='stand-native-sections-v1')throw Error('Unexpected native section schema');
  for(const key of ['left_wall_x','right_wall_x','wall_span','base_width','base_depth'])if(data.dimensions_mm[key]!==model.dimensions_mm[key])throw Error('Section/model dimension mismatch: '+key);
  const controls=document.querySelector('#section-controls');
  controls.innerHTML=data.sections.map((s,i)=>`<button data-section="${s.id}" aria-pressed="${i===0}">${s.label}</button>`).join('');
  const render=section=>{
    document.querySelector('#section-plane').textContent=section.description+` Cut coordinate: ${section.plane==='XY'?'Z':'Y'} = ${fmt(section.offset_mm)} mm.`;
    document.querySelector('#section-note').textContent=section.note;
    document.querySelector('#section-full-title').textContent=section.label+' · complete cut';
    document.querySelector('#section-detail-title').textContent=section.id==='base'?'Pilot detail':'Highlighted detail';
    draw(document.querySelector('#section-full'),section,data,false);draw(document.querySelector('#section-detail'),section,data,true);
    for(const b of controls.querySelectorAll('button'))b.setAttribute('aria-pressed',b.dataset.section===section.id);
    window.standSectionReview={data,section};
  };
  controls.onclick=e=>{const id=e.target.closest('button')?.dataset.section;if(id)render(data.sections.find(s=>s.id===id))};
  render(data.sections[0]);
}
