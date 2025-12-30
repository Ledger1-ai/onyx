import React from 'react';
import Header from '../../components/Header';
import NavigationDock from '@/components/Navigation/NavigationDock';

export default function UnderworldLayout({
    children,
}: {
    children: React.ReactNode;
}) {
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
