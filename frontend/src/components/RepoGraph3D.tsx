import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Line } from '@react-three/drei'
import * as THREE from 'three'

const NODES = [
  { pos: [-3, 0.5, -1], color: '#3b82f6', label: 'frontend' },
  { pos: [0, 1.2, 0.5], color: '#6366f1', label: 'api' },
  { pos: [3, 0.3, -0.5], color: '#8b5cf6', label: 'worker' },
  { pos: [-1.5, -0.8, 2], color: '#06b6d4', label: 'docs' },
  { pos: [2, -0.5, 1.5], color: '#10b981', label: 'tests' },
  { pos: [-2.5, 0, -2], color: '#f59e0b', label: 'config' },
]

const EDGES = [[0, 1], [1, 2], [3, 1], [4, 2], [5, 0], [3, 5], [4, 1]]

function Node({ position, color, label }: { position: [number, number, number]; color: string; label: string }) {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(clock.elapsedTime * 0.5 + position[0]) * 0.08
    }
  })

  return (
    <group position={position}>
      <mesh ref={meshRef}>
        <sphereGeometry args={[0.12, 16, 16]} />
        <meshPhysicalMaterial color={color} emissive={color} emissiveIntensity={0.3} metalness={0.3} roughness={0.2} />
      </mesh>
      <sprite scale={[0.6, 0.3, 1]} position={[0, -0.3, 0]}>
        <spriteMaterial>
          <canvasTexture attach="map">
            <canvas id={`label-${label}`} width={64} height={32} style={{ display: 'none' }} />
          </canvasTexture>
        </spriteMaterial>
      </sprite>
    </group>
  )
}

function Edge({ start, end }: { start: [number, number, number]; end: [number, number, number] }) {
  const points = useMemo(() => [new THREE.Vector3(...start), new THREE.Vector3(...end)], [start, end])
  return (
    <Line
      points={points}
      color="#1f1f23"
      lineWidth={0.5}
      transparent
      opacity={0.6}
    />
  )
}

function Scene() {
  const groupRef = useRef<THREE.Group>(null)

  useFrame(({ clock }) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(clock.elapsedTime * 0.08) * 0.15
    }
  })

  return (
    <group ref={groupRef}>
      <ambientLight intensity={0.3} />
      <pointLight position={[2, 3, 2]} intensity={0.8} color="#3b82f6" />
      <pointLight position={[-2, -1, -2]} intensity={0.4} color="#8b5cf6" />
      {NODES.map((node, i) => (
        <Node key={i} position={node.pos as [number, number, number]} color={node.color} label={node.label} />
      ))}
      {EDGES.map(([i, j], k) => (
        <Edge key={k} start={NODES[i].pos as [number, number, number]} end={NODES[j].pos as [number, number, number]} />
      ))}
    </group>
  )
}

export function RepoGraph3D({ className = '' }: { className?: string }) {
  return (
    <div className={`${className}`}>
      <Canvas camera={{ position: [0, 0, 5], fov: 45 }} dpr={[1, 1.5]} gl={{ antialias: true, alpha: true }}>
        <Scene />
        <OrbitControls enableZoom={false} enablePan={false} enableRotate={false} autoRotate={false} />
      </Canvas>
    </div>
  )
}
