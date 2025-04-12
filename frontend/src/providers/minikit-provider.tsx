'use client' // Required for Next.js

import { ReactNode, useEffect } from 'react'
import { MiniKit } from '@worldcoin/minikit-js'

export default function MiniKitProvider({ children }: { children: ReactNode }) {
	useEffect(() => {
		// Passing appId in the install is optional
		// but allows you to access it later via `window.MiniKit.appId`
		const appId = 'your-app-id'; // Replace 'your-app-id' with your actual app ID
		MiniKit.install(appId)
	}, [])

	return <>{children}</>
}
