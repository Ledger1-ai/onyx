import React from 'react';
import { X } from 'lucide-react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
    footer?: React.ReactNode;
}

export default function Modal({ isOpen, onClose, title, children, footer }: ModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="glass-panel w-full max-w-md rounded-xl overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200 border border-white/10 bg-gray-900/90">
                <div className="flex items-center justify-between p-4 border-b border-white/10 bg-white/5">
                    <h3 className="font-orbitron font-bold text-lg text-white">{title}</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <div className="p-6 text-gray-200">
                    {children}
                </div>
                {footer && (
                    <div className="p-4 border-t border-white/10 bg-black/20 flex justify-end space-x-2">
                        {footer}
                    </div>
                )}
            </div>
        </div>
    );
}
