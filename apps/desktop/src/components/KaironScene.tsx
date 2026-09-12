import { useEffect, useRef } from "react";
import * as THREE from "three";
import type { KaironState } from "../types/kairon";

interface KaironSceneProps {
  state: KaironState;
}

const stateColors: Record<KaironState, number> = {
  idle: 0x00dfe3,
  listening_for_wake_word: 0x00dfe3,
  wake_word_detected: 0x79ffff,
  listening: 0x79ffff,
  processing: 0x28d9ff,
  thinking: 0xc7fcff,
  speaking: 0xffc457,
  executing: 0xffc457,
  error: 0xff6262,
  offline: 0x556668,
};

const activeStates = new Set<KaironState>([
  "wake_word_detected",
  "listening",
  "processing",
  "thinking",
  "speaking",
  "executing",
]);

function createRing(radius: number, opacity: number, color: number, thickness = 0.012) {
  return new THREE.Mesh(
    new THREE.TorusGeometry(radius, thickness, 5, 240),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity }),
  );
}

export function KaironScene({ state }: KaironSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stateRef = useRef(state);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x010607);
    scene.fog = new THREE.FogExp2(0x010607, 0.085);

    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 50);
    camera.position.set(0, 0, 9.2);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "high-performance",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.65));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.domElement.className = "kairon-scene__canvas";
    renderer.domElement.setAttribute("aria-hidden", "true");
    container.appendChild(renderer.domElement);

    const core = new THREE.Group();
    core.position.y = -0.05;
    scene.add(core);

    const signalMaterial = new THREE.MeshBasicMaterial({
      color: stateColors[stateRef.current],
      transparent: true,
      opacity: 0.82,
      wireframe: true,
    });
    const innerMaterial = new THREE.MeshBasicMaterial({
      color: 0x8effff,
      transparent: true,
      opacity: 0.42,
      wireframe: true,
    });
    const coreShell = new THREE.Mesh(new THREE.IcosahedronGeometry(0.82, 3), signalMaterial);
    const innerCore = new THREE.Mesh(new THREE.IcosahedronGeometry(0.52, 2), innerMaterial);
    core.add(coreShell, innerCore);

    const ringGroup = new THREE.Group();
    const ringRadii = [1.08, 1.25, 1.55, 1.83, 2.18, 2.5, 2.84];
    const rings = ringRadii.map((radius, index) => {
      const ring = createRing(radius, 0.16 + (index % 3) * 0.08, 0x00dfe3, index === 2 ? 0.02 : 0.01);
      ring.rotation.z = index * 0.19;
      ringGroup.add(ring);
      return ring;
    });
    core.add(ringGroup);

    const tickGeometry = new THREE.BufferGeometry();
    const tickPositions: number[] = [];
    for (let index = 0; index < 96; index += 1) {
      const angle = (index / 96) * Math.PI * 2;
      const major = index % 8 === 0;
      const innerRadius = major ? 2.16 : 2.28;
      const outerRadius = major ? 2.48 : 2.4;
      tickPositions.push(
        Math.cos(angle) * innerRadius,
        Math.sin(angle) * innerRadius,
        0,
        Math.cos(angle) * outerRadius,
        Math.sin(angle) * outerRadius,
        0,
      );
    }
    tickGeometry.setAttribute("position", new THREE.Float32BufferAttribute(tickPositions, 3));
    const ticks = new THREE.LineSegments(
      tickGeometry,
      new THREE.LineBasicMaterial({ color: 0x9effff, transparent: true, opacity: 0.42 }),
    );
    core.add(ticks);

    const arcGroup = new THREE.Group();
    for (let index = 0; index < 18; index += 1) {
      const angle = (index / 18) * Math.PI * 2;
      const arc = new THREE.Mesh(
        new THREE.BoxGeometry(index % 3 === 0 ? 0.32 : 0.16, 0.028, 0.018),
        new THREE.MeshBasicMaterial({
          color: index % 5 === 0 ? 0xffffff : 0x00dfe3,
          transparent: true,
          opacity: index % 3 === 0 ? 0.7 : 0.35,
        }),
      );
      arc.position.set(Math.cos(angle) * 1.7, Math.sin(angle) * 1.7, 0.02);
      arc.rotation.z = angle + Math.PI / 2;
      arcGroup.add(arc);
    }
    core.add(arcGroup);

    const orbitalNodes: THREE.Mesh[] = [];
    for (let index = 0; index < 8; index += 1) {
      const angle = (index / 8) * Math.PI * 2 + 0.18;
      const node = createRing(0.1, 0.65, index === 2 ? 0xffc457 : 0x00dfe3, 0.015);
      node.position.set(Math.cos(angle) * 3.05, Math.sin(angle) * 3.05, 0);
      core.add(node);
      orbitalNodes.push(node);
    }

    const starsGeometry = new THREE.BufferGeometry();
    const starPositions: number[] = [];
    for (let index = 0; index < 260; index += 1) {
      const angle = index * 2.399;
      const radius = 3.3 + ((index * 37) % 90) / 18;
      starPositions.push(
        Math.cos(angle) * radius,
        Math.sin(angle) * radius * 0.72,
        -1.2 - (index % 7) * 0.25,
      );
    }
    starsGeometry.setAttribute("position", new THREE.Float32BufferAttribute(starPositions, 3));
    const stars = new THREE.Points(
      starsGeometry,
      new THREE.PointsMaterial({ color: 0x7cd9dc, size: 0.018, transparent: true, opacity: 0.3 }),
    );
    scene.add(stars);

    const pointer = new THREE.Vector2();
    const onPointerMove = (event: PointerEvent) => {
      pointer.x = (event.clientX / window.innerWidth - 0.5) * 0.12;
      pointer.y = (event.clientY / window.innerHeight - 0.5) * 0.08;
    };
    window.addEventListener("pointermove", onPointerMove, { passive: true });

    const resize = () => {
      const width = container.clientWidth;
      const height = container.clientHeight;
      renderer.setSize(width, height, false);
      camera.aspect = width / Math.max(height, 1);
      camera.updateProjectionMatrix();
    };
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
    resize();

    const clock = new THREE.Clock();
    let animationFrame = 0;
    const render = () => {
      const elapsed = clock.getElapsedTime();
      const currentState = stateRef.current;
      const active = activeStates.has(currentState);
      const speed = currentState === "thinking" ? 1.8 : currentState === "speaking" ? 1.3 : 0.7;
      const motion = reducedMotion.matches ? 0 : 1;

      coreShell.rotation.x = elapsed * 0.18 * speed * motion;
      coreShell.rotation.y = elapsed * 0.26 * speed * motion;
      innerCore.rotation.x = -elapsed * 0.3 * speed * motion;
      innerCore.rotation.z = elapsed * 0.2 * speed * motion;
      ringGroup.rotation.z = elapsed * 0.025 * speed * motion;
      ticks.rotation.z = -elapsed * 0.045 * speed * motion;
      arcGroup.rotation.z = elapsed * 0.075 * speed * motion;
      stars.rotation.z = -elapsed * 0.004 * motion;
      orbitalNodes.forEach((node, index) => {
        node.scale.setScalar(0.9 + Math.sin(elapsed * 1.8 + index) * 0.12 * motion);
      });

      const pulse = active && motion ? 1 + Math.sin(elapsed * 3.4) * 0.022 : 1;
      coreShell.scale.setScalar(pulse);
      innerCore.scale.setScalar(1 + (pulse - 1) * 1.8);
      core.rotation.x += (pointer.y - core.rotation.x) * 0.025;
      core.rotation.y += (pointer.x - core.rotation.y) * 0.025;

      const targetColor = new THREE.Color(stateColors[currentState]);
      signalMaterial.color.lerp(targetColor, 0.06);
      rings.forEach((ring) => {
        if (ring.material instanceof THREE.MeshBasicMaterial) {
          ring.material.color.lerp(targetColor, 0.035);
        }
      });

      renderer.render(scene, camera);
      animationFrame = window.requestAnimationFrame(render);
    };
    render();

    return () => {
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener("pointermove", onPointerMove);
      resizeObserver.disconnect();
      scene.traverse((object) => {
        if (
          object instanceof THREE.Mesh
          || object instanceof THREE.LineSegments
          || object instanceof THREE.Points
        ) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        }
      });
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  return <div className="kairon-scene" ref={containerRef} />;
}
