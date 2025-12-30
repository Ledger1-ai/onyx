"use client";

// import { useEffect, useState } from 'react';
// import { io, Socket } from 'socket.io-client';

export const useSocket = () => {
    // Socket disabled for queue-based architecture migration
    // Polling will be used instead
    return { socket: null, isConnected: false };
};
