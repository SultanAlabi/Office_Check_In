const CACHE_NAME = 'check-in-system-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/style.css',
    '/static/js/script.js',
    '/static/favicon.ico',
    '/mobile_check_in',
    '/dashboard'
];

// Install Service Worker
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Opened cache');
                return cache.addAll(ASSETS_TO_CACHE);
            })
    );
});

// Activate Service Worker
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Fetch Event Strategy
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached version if available
                if (response) {
                    return response;
                }

                // Clone the request
                const fetchRequest = event.request.clone();

                // Make network request
                return fetch(fetchRequest).then(
                    (response) => {
                        // Check if valid response
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response
                        const responseToCache = response.clone();

                        // Cache the response
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    }
                );
            })
            .catch(() => {
                // Return offline page if no connection
                if (event.request.mode === 'navigate') {
                    return caches.match('/mobile_check_in');
                }
            })
    );
});

// Handle sync events for offline functionality
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-pending-actions') {
        event.waitUntil(
            syncPendingActions()
                .catch(error => {
                    console.error('Sync failed:', error);
                })
        );
    }
});

// Helper function to sync pending actions
async function syncPendingActions() {
    try {
        const pendingActions = await getPendingActions();
        
        for (const action of pendingActions) {
            try {
                const response = await fetch(action.url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(action.data)
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                // Remove synced action
                await removePendingAction(action);
            } catch (error) {
                console.error('Failed to sync action:', error);
                // Keep the action in the queue for retry
            }
        }
    } catch (error) {
        console.error('Failed to get pending actions:', error);
        throw error;
    }
}

// Helper functions for managing pending actions
async function getPendingActions() {
    const db = await openDB();
    return db.getAll('pending-actions');
}

async function removePendingAction(action) {
    const db = await openDB();
    return db.delete('pending-actions', action.id);
}

// IndexedDB helper
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('check-in-system', 1);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('pending-actions')) {
                db.createObjectStore('pending-actions', { keyPath: 'id', autoIncrement: true });
            }
        };
    });
} 