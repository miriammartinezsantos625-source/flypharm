/* FLYPHARM · monta el cuerpo de flybody (Janelia/DeepMind) como jerarquía Three.js.
   MuJoCo: x adelante, y izquierda, z arriba, cuaternión (w,x,y,z).
   Three:  y arriba, cuaternión (x,y,z,w).  El grupo raíz hace la conversión. */
function construirMosca(datos, THREE){
  const b64 = s => { const b=atob(s), u=new Uint8Array(b.length); for(let i=0;i<b.length;i++) u[i]=b.charCodeAt(i); return u.buffer; };
  const geos = {};
  for(const m of datos.mallas){
    const q = new Uint16Array(b64(m.pos)), n = m.nv, pos = new Float32Array(n*3);
    for(let i=0;i<n;i++) for(let k=0;k<3;k++) pos[i*3+k] = m.min[k] + q[i*3+k]/65535*(m.max[k]-m.min[k]);
    const idx = m.idx32 ? new Uint32Array(b64(m.idx)) : new Uint16Array(b64(m.idx));
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos,3));
    g.setIndex(new THREE.BufferAttribute(idx,1));
    g.computeVertexNormals();
    geos[m.name] = g;
  }
  const mat = {};
  // Paleta oscura: cutícula negro-carbón, vientre gris oscuro, ojos rojos, membrana translúcida.
  const OSCURA = { '0.674 0.35 0.143 1':'0.10 0.09 0.085 1', '0.799 0.61 0.386 1':'0.20 0.18 0.17 1',
                   '0.202 0.0782 0.0262 1':'0.13 0.11 0.10 1', '0.32 0.22 0.13 1':'0.12 0.10 0.09 1',
                   '0.63 0.47 0.31 1':'0.10 0.09 0.085 1', '0.78 0.64 0.45 1':'0.20 0.18 0.17 1',
                   '0.36 0.26 0.16 0.9':'0.15 0.13 0.12 0.9', '0.539 0.686 0.8 0.4':'0.50 0.58 0.66 0.22' };
  const material = rgba0 => {
    const rgba = OSCURA[rgba0] || rgba0;
    const [r,g,b,a] = rgba.split(' ').map(Number), k = rgba;
    if(!mat[k]) mat[k] = new THREE.MeshStandardMaterial({ color:new THREE.Color(r,g,b), roughness:.55, metalness:.08,
                          transparent:a<1, opacity:a, side:THREE.DoubleSide, depthWrite:a>=1 });
    return mat[k];
  };
  // Capas que en flybody se superponen exactamente al cuerpo (pelos, cerdas): tras decimar
  // producen z-fighting, así que no se dibujan. Los ojos sí, con prioridad de profundidad.
  const OMITIR = /_black$|bristle/;
  const ENCIMA = /head_red|head_ocelli|_lower$|membrane/;
  const Q = q => new THREE.Quaternion(q[1],q[2],q[3],q[0]);
  const cuerpos = {}, q0 = {}, joints = {};
  for(const p of datos.partes){
    const o = new THREE.Group(); o.name = p.name;
    o.position.set(...p.pos); o.quaternion.copy(Q(p.quat));
    q0[p.name] = o.quaternion.clone(); joints[p.name] = p.joints;
    for(const g of p.geoms){
      if(OMITIR.test(g.mesh)) continue;
      const m = new THREE.Mesh(geos[g.mesh], material(g.rgba));
      if(ENCIMA.test(g.mesh)){ m.material = m.material.clone(); m.material.polygonOffset=true;
        m.material.polygonOffsetFactor=-2; m.material.polygonOffsetUnits=-2; m.renderOrder=1; }
      m.position.set(...g.pos); m.quaternion.copy(Q(g.quat)); o.add(m);
    }
    cuerpos[p.name] = o;
    (p.parent ? cuerpos[p.parent] : null)?.add(o);
  }
  const raizMuJoCo = cuerpos[datos.partes[0].name];
  const raiz = new THREE.Group(); raiz.name = 'mosca';
  raiz.add(raizMuJoCo);
  raiz.rotation.x = -Math.PI/2;                        // z-arriba -> y-arriba
  /* pose(nombre, {joint: ángulo}) — rota el cuerpo alrededor del eje de cada articulación */
  const tmp = new THREE.Quaternion(), ax = new THREE.Vector3();
  function pose(nombre, angulos){
    const o = cuerpos[nombre]; if(!o) return;
    o.quaternion.copy(q0[nombre]);
    for(const j of joints[nombre]){
      const a = angulos[j.name]; if(!a) continue;
      ax.set(...j.axis).normalize(); tmp.setFromAxisAngle(ax, a); o.quaternion.multiply(tmp);
    }
  }
  return { raiz, cuerpos, joints, pose };
}
