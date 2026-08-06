import { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import ThreeScene from './ThreeScene'

export default function BlueprintViewer({ blueprint, activeLayers, selectedRoom }) {
  return (
    <div className="w-full h-full">
      <Canvas camera={{ position: [15, 15, 15], fov: 45 }}>
        <color attach="background" args={['#0f172a']} />
        <ambientLight intensity={0.6} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <Suspense fallback={null}>
          <ThreeScene 
            blueprint={blueprint} 
            activeLayers={activeLayers}
            selectedRoom={selectedRoom}
          />
        </Suspense>
        <OrbitControls />
        <gridHelper args={[50, 50, '#334155', '#1e293b']} />
      </Canvas>
    </div>
  )
}
