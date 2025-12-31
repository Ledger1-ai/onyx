"use client";

import React from 'react';
import { usePathname } from 'next/navigation';
import Header from '../../components/Header';
import NavigationDock from '@/components/Navigation/NavigationDock';

export default function UnderworldLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();
    const isGateway = pathname === '/underworld/gateway';

    if (isGateway) {
        return <div className="min-h-screen bg-black relative">{children}</div>;
    }

    return (
        <div className="min-h-screen bg-black relative">
            <Header />
            <div className="pb-24"> {/* Padding for Dock */}
                {children}
            </div>
            <NavigationDock />
        </div>
    );
}
