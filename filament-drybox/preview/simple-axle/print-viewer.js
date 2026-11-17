import * as T from 'three';
import {OrbitControls} from '../vendor/OrbitControls.js';
const inch=n=>(n/25.4).toFixed(3)+'″';
const format=n=>Number(n.toFixed(2));
const fetchJson=async path=>{const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error(path+' HTTP '+r.status);return r.json()};
const host=document.querySelector('#print-parts');
try{
  const data=await fetchJson(document.querySelector('[data-print-review]')?.dataset.printReview || './print-review.json');
  if(data.schema!=='drybox-print-review-v1')throw Error('Unexpected print-review schema');
  document.querySelector('#preparation-status').textContent=data.status;
  document.querySelector('#print-summary').textContent=data.summary;
  document.querySelector('#print-settings').textContent=data.settings;
  document.querySelector('#print-estimate').textContent=data.estimate;
  document.querySelector('#print-downloads').innerHTML=`<a href="${data.project}">Editable proposed plate</a> · <a href="${data.sliced}">Sliced review plate</a>`;
  document.querySelector('#print-audit').innerHTML=data.parts.map(p=>`<tr><th scope="row">${p.label}</th><td>${p.audit}</td><td>${p.first_fit}</td></tr>`).join('');
  const views=[];
  for(const part of data.parts){
    const article=document.createElement('article');article.className='print-part';
    article.innerHTML=`<h3>${part.label}</h3><div class="print-canvas" aria-label="Rotatable ${part.label} in print orientation">${part.still ? `<img class="print-still" src="${part.still}" alt="${part.label} on the print bed with its proposed support scaffolding">` : ""}</div><div class="print-tools"><button class="supports" aria-pressed="true">Show supports</button><button class="reset">Reset view</button><a href="${part.stl}">STL</a></div><p>${part.orientation}</p><p class="fine">Footprint ${format(part.size_mm[0])} × ${format(part.size_mm[1])} mm (${inch(part.size_mm[0])} × ${inch(part.size_mm[1])}); height ${format(part.size_mm[2])} mm / ${inch(part.size_mm[2])}.</p><p class="fine">${part.support_note}</p>`;
    host.appendChild(article);const canvasHost=article.querySelector('.print-canvas');
    const scene=new T.Scene();scene.background=new T.Color('#e3e6e9');const renderer=new T.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));canvasHost.appendChild(renderer.domElement);
    const camera=new T.OrthographicCamera(-1,1,1,-1,.1,5000);camera.up.set(0,0,1);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
    scene.add(new T.HemisphereLight(0xffffff,0x8c9399,2));for(const l of data.look.lights){const d=new T.DirectionalLight(0xffffff,l.energy);d.position.fromArray(l.towards_light).multiplyScalar(300);scene.add(d)}
    const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.Float32BufferAttribute(part.mesh.vertices.flat(),3));geometry.setIndex(part.mesh.triangles.flat());geometry.computeVertexNormals();const mesh=new T.Mesh(geometry,new T.MeshStandardMaterial({color:part.color,roughness:.55,side:T.DoubleSide,flatShading:true}));scene.add(mesh);
    const supportGeometry=new T.BufferGeometry();supportGeometry.setAttribute('position',new T.Float32BufferAttribute(part.support_segments.flat(2),3));const support=new T.LineSegments(supportGeometry,new T.LineBasicMaterial({color:'#c1bba9',transparent:true,opacity:.85}));scene.add(support);if(!part.support_segments.length){support.visible=false;const button=article.querySelector('.supports');button.disabled=true;button.textContent='No supports';button.setAttribute('aria-pressed','false')}
    const context=part.context_bounds_mm;const bed=new T.Mesh(new T.PlaneGeometry(context[1][0]-context[0][0],context[1][1]-context[0][1]),new T.MeshStandardMaterial({color:'#888888',roughness:.6,side:T.DoubleSide}));bed.position.set((context[0][0]+context[1][0])/2,(context[0][1]+context[1][1])/2,-.12);scene.add(bed);
    const grid=new T.GridHelper(Math.max(context[1][0]-context[0][0],context[1][1]-context[0][1]),14,0x899995,0xbfc8c3);grid.rotation.x=Math.PI/2;grid.position.copy(bed.position);grid.position.z=-.1;scene.add(grid);
    const box=new T.Box3().setFromObject(mesh),center=box.getCenter(new T.Vector3()),size=box.getSize(new T.Vector3());
    function reset(){const aspect=canvasHost.clientWidth/canvasHost.clientHeight,c=part.camera,imageAspect=c.resolution[0]/c.resolution[1];let hw=imageAspect>=1?c.ortho_scale/2:c.ortho_scale*imageAspect/2,hh=imageAspect>=1?hw/imageAspect:c.ortho_scale/2;hw=Math.max(hw,hh*aspect);hh=hw/aspect;camera.left=-hw;camera.right=hw;camera.top=hh;camera.bottom=-hh;camera.position.fromArray(c.position);controls.target.fromArray(c.target);camera.zoom=1;camera.updateProjectionMatrix();controls.update()}
    const view={scene,renderer,camera,controls,part,article,mesh,support,live:!part.still,visible:false};new IntersectionObserver(entries=>{view.visible=entries[0].isIntersecting}).observe(canvasHost);
    const showLive=()=>{view.live=true;const still=canvasHost.querySelector('.print-still');if(still)still.remove()};canvasHost.addEventListener('pointerdown',showLive);article.querySelector('.reset').onclick=()=>{showLive();reset()};article.querySelector('.supports').onclick=e=>{showLive();support.visible=!support.visible;e.target.setAttribute('aria-pressed',support.visible)};
    new ResizeObserver(()=>{renderer.setSize(canvasHost.clientWidth,canvasHost.clientHeight);reset()}).observe(canvasHost);reset();views.push(view);
  }
  function animate(){requestAnimationFrame(animate);for(const v of views){if(v.live&&v.visible){v.controls.update();v.renderer.render(v.scene,v.camera)}}}animate();window.dryboxPrintReview={data,views};
}catch(error){document.querySelector('#print-summary').textContent='Unable to load current print preparation: '+error.message;throw error}
