const CACHE_NAME = 'check-in-system-v1';
const CACHE_URLS = [
    '/',
    '/static/css/style.css',
    '/static/js/script.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js',
    'https://code.jquery.com/jquery-3.6.0.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    '/mobile_check_in'
];

// Install Service Worker
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Cache opened');
                return cache.addAll(CACHE_URLS).catch(error => {
                    console.error('Failed to cache resources:', error);
                    // Continue installation even if some resources fail to cache
                    return Promise.resolve();
                });
            })
            .catch(error => {
                console.error('Service worker installation failed:', error);
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
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Fetch Event Handler
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    // Handle the fetch event
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached response if found
                if (response) {
                    return response;
                }

                // Clone the request because it can only be used once
                const fetchRequest = event.request.clone();

                // Make network request
                return fetch(fetchRequest)
                    .then((response) => {
                        // Check if response is valid
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response because it can only be used once
                        const responseToCache = response.clone();

                        // Cache the new response
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            })
                            .catch(error => {
                                console.error('Failed to cache response:', error);
                            });

                        return response;
                    })
                    .catch(error => {
                        console.error('Fetch failed:', error);
                        // Return a custom offline page or fallback content
                        return caches.match('/offline.html');
                    });
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