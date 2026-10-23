"use client";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

const VERTEX = `#version 300 es
void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(p*2.-1.,0.,1.);}`;
const FRAGMENT = `#version 300 es
precision highp float;
precision highp sampler3D;
uniform sampler3D uNoise;
uniform vec2 uView,uCenter,uHole;
uniform float uScale,uTime;
uniform vec3 uSage,uStone,uLift;
out vec4 result;
void main(){
 vec2 screen=gl_FragCoord.xy/uScale;
 vec2 q=(screen-uCenter)/uHole;
 float radius=length(q);
 if(radius<.83||radius>3.5){result=vec4(0.);return;}
 vec3 eye=vec3(0.,2.4,0.);
 vec3 ray=normalize(vec3(q.x,-2.4,q.y));
 float stepSize=.76/36./(-ray.y);
 float t=(2.4-.38)/(-ray.y);
 t+=fract(52.98*fract(dot(gl_FragCoord.xy,vec2(.0671,.00584))))*stepSize;
 vec3 colour=vec3(0.);float remaining=1.;
 for(int i=0;i<36;i++){
  vec3 p=eye+ray*t;t+=stepSize;
  float r=length(p.xz);if(r<.93||r>3.2)continue;
  float angle=atan(p.z,p.x)-uTime*.025;
  float turn=(angle-3.6/(r+.55))/6.2831853;
  float height=p.y-.24*p.z/max(r,.01);
  vec4 low=texture(uNoise,vec3(turn*3.+uTime*.007,height*.7,r*.5));
  vec4 fine=texture(uNoise,vec3(turn*12.,height*.12,r*1.7)+(low.rgb-.5)*.65);
  float n=dot(low,vec4(.38,.24,0.,0.))+dot(fine,vec4(0.,0.,.24,.14));
  float density=smoothstep(.31,.66,n);
  density*=smoothstep(.94,1.26,r)*(1.-smoothstep(1.5,3.2,r));
  density*=exp(-height*height/.025);
  density*=.72+.28*cos(2.*angle+log(r)*5.);
  float wheel=.5+.5*cos(angle+.55);
  vec3 pigment=mix(uSage,uStone,wheel);
  pigment=mix(pigment,uLift,clamp((1.7-r)*.5+fine.g*.2,0.,.6));
  float alpha=1.-exp(-density*stepSize*7.);
  colour+=remaining*alpha*pigment;remaining*=1.-alpha;
 }
 float alpha=1.-remaining;
 result=vec4(colour,alpha);
}`;

function noiseVolume() {
  const side = 32, data = new Uint8Array(side ** 3 * 4);
  let seed = 1729;
  const random = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
  const mix = (a: number, b: number, t: number) => a + (b - a) * t;
  for (let channel = 0; channel < 4; channel++) {
    const cells = 4 << channel;
    const grid = Float32Array.from({ length: cells ** 3 }, random);
    const get = (x: number, y: number, z: number) => grid[((z % cells) * cells + y % cells) * cells + x % cells];
    for (let z = 0; z < side; z++) for (let y = 0; y < side; y++) for (let x = 0; x < side; x++) {
      const xx = x * cells / side, yy = y * cells / side, zz = z * cells / side;
      const a = Math.floor(xx), b = Math.floor(yy), c = Math.floor(zz);
      const smooth = (v: number) => v * v * (3 - 2 * v);
      const dx = smooth(xx - a), dy = smooth(yy - b), dz = smooth(zz - c);
      const slice = (k: number) => mix(mix(get(a, b, k), get(a + 1, b, k), dx), mix(get(a, b + 1, k), get(a + 1, b + 1, k), dx), dy);
      data[((z * side + y) * side + x) * 4 + channel] = Math.round(mix(slice(c), slice(c + 1), dz) * 255);
    }
  }
  return data;
}

export function Atmosphere() {
  const path = usePathname();
  const visible = path === "/" || path === "/login" || path === "/signup";
  const canvas = useRef<HTMLCanvasElement>(null);
  const [ready, setReady] = useState(false);
  const [generation, setGeneration] = useState(0);
  useEffect(() => {
    const element = canvas.current;
    if (!visible || !element) return;
    const gl = element.getContext("webgl2", { alpha: true, antialias: false, premultipliedAlpha: true });
    if (!gl) return;
    const shader = (type: number, source: string) => {
      const s = gl.createShader(type)!; gl.shaderSource(s, source); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { gl.deleteShader(s); return null; }
      return s;
    };
    const vertex = shader(gl.VERTEX_SHADER, VERTEX), fragment = shader(gl.FRAGMENT_SHADER, FRAGMENT);
    if (!vertex || !fragment) { if (vertex) gl.deleteShader(vertex); if (fragment) gl.deleteShader(fragment); return; }
    const program = gl.createProgram()!;
    gl.attachShader(program, vertex); gl.attachShader(program, fragment); gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) { gl.deleteProgram(program); gl.deleteShader(vertex); gl.deleteShader(fragment); return; }
    gl.useProgram(program);
    const texture = gl.createTexture()!;
    gl.bindTexture(gl.TEXTURE_3D, texture);
    gl.texImage3D(gl.TEXTURE_3D, 0, gl.RGBA8, 32, 32, 32, 0, gl.RGBA, gl.UNSIGNED_BYTE, noiseVolume());
    gl.texParameteri(gl.TEXTURE_3D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_3D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    for (const parameter of [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T, gl.TEXTURE_WRAP_R]) gl.texParameteri(gl.TEXTURE_3D, parameter, gl.REPEAT);
    gl.uniform1i(gl.getUniformLocation(program, "uNoise"), 0);
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    const uniform = (name: string) => gl.getUniformLocation(program, name);
    const timeUniform = uniform("uTime");
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const suppressed = ["(prefers-contrast: more)", "(prefers-reduced-transparency: reduce)", "(forced-colors: active)"].map(query => window.matchMedia(query));
    let frame = 0, time = 0, last = performance.now(), stopped = false;
    const geometry = () => {
      const width = innerWidth, height = innerHeight, scale = .62;
      element.width = Math.round(width * scale); element.height = Math.round(height * scale);
      gl.viewport(0, 0, element.width, element.height);
      gl.uniform2f(uniform("uView"), width, height); gl.uniform1f(uniform("uScale"), scale);
      const copy = document.querySelector(".landing-hero > div, .auth-layout");
      const r = copy?.getBoundingClientRect();
      gl.uniform2f(uniform("uCenter"), r ? r.x + r.width / 2 : width / 2, r ? height - r.y - r.height / 2 : height * .55);
      gl.uniform2f(uniform("uHole"), r ? Math.max(220, r.width / 2 + 80) : width * .3, r ? Math.max(160, Math.min(r.height / 2 + 64, height * .46)) : height * .22);
    };
    const swatch = document.createElement("canvas"); swatch.width = swatch.height = 1;
    const paint = swatch.getContext("2d", { willReadFrequently: true });
    const colours = () => {
      const style = getComputedStyle(document.documentElement);
      if (!paint) return;
      for (const [name, property] of [["uSage", "--field-sage"], ["uStone", "--field-stone"], ["uLift", "--field-lift"]]) {
        paint.clearRect(0, 0, 1, 1);
        paint.fillStyle = style.getPropertyValue(property).trim(); paint.fillRect(0, 0, 1, 1);
        const values = paint.getImageData(0, 0, 1, 1).data;
        gl.uniform3f(uniform(name), values[0] / 255, values[1] / 255, values[2] / 255);
      }
    };
    const draw = (now = performance.now()) => {
      if (stopped) return;
      if (document.hidden || suppressed.some(value => value.matches)) { last = now; return; }
      if (!media.matches) time += Math.min((now - last) / 1000, .05);
      last = now; gl.uniform1f(timeUniform, time);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLES, 0, 3);
      if (!media.matches && !document.hidden) frame = requestAnimationFrame(draw);
    };
    const refresh = () => { cancelAnimationFrame(frame); geometry(); colours(); draw(); };
    const theme = new MutationObserver(refresh);
    theme.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    const size = new ResizeObserver(refresh);
    size.observe(document.getElementById("main-content") || document.body);
    const scheme = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", refresh); scheme.addEventListener("change", refresh);
    suppressed.forEach(value => value.addEventListener("change", refresh));
    window.addEventListener("resize", refresh); document.addEventListener("visibilitychange", refresh);
    const lost = (event: Event) => { event.preventDefault(); stopped = true; cancelAnimationFrame(frame); setReady(false); };
    const restored = () => setGeneration(value => value + 1);
    element.addEventListener("webglcontextlost", lost); element.addEventListener("webglcontextrestored", restored);
    geometry(); colours(); setReady(true); draw();
    const settled = window.setTimeout(refresh, 1350);
    return () => {
      stopped = true; cancelAnimationFrame(frame); clearTimeout(settled);
      theme.disconnect(); size.disconnect(); media.removeEventListener("change", refresh); scheme.removeEventListener("change", refresh);
      suppressed.forEach(value => value.removeEventListener("change", refresh));
      window.removeEventListener("resize", refresh); document.removeEventListener("visibilitychange", refresh);
      element.removeEventListener("webglcontextlost", lost); element.removeEventListener("webglcontextrestored", restored);
      gl.deleteTexture(texture); gl.deleteProgram(program); gl.deleteShader(vertex); gl.deleteShader(fragment);
      setReady(false);
    };
  }, [visible, path, generation]);
  return <div className={`atmosphere${ready ? " is-rendered" : ""}`} aria-hidden="true">
    <canvas ref={canvas} className="volume-field" />
    <svg className="atmosphere-grain" width="100%" height="100%" focusable="false"><defs><filter id="turio-grain"><feTurbulence type="fractalNoise" baseFrequency=".65" numOctaves="3" stitchTiles="stitch" /><feColorMatrix type="saturate" values="0" /></filter></defs><rect width="100%" height="100%" filter="url(#turio-grain)" /></svg>
  </div>;
}
