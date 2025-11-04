/**
 * CfpaZMS Mobile App - Service Worker
 * يدعم العمل بدون إنترنت والتخزين المؤقت والإشعارات المباشرة
 */

const CACHE_NAME = 'cfpa-zms-v2';
const RUNTIME_CACHE = 'cfpa-zms-runtime-v2';
const API_CACHE = 'cfpa-zms-api-v2';
const DYNAMIC_CACHE = 'cfpa-zms-dynamic-v2';

const urlsToCache = [
  '/',
  '/mobile/app',
  '/mobile/app/assets',
  '/mobile/app/scan',
  '/mobile/app/dashboard',
  '/static/css/mobile.css',
  '/static/js/mobile.js',
  '/static/js/camera-scanner.js',
  '/static/images/icon-192x192.png',
  '/static/images/icon-512x512.png'
];

// تثبيت Service Worker
self.addEventListener('install', event => {
  console.log('Service Worker Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .catch(error => console.error('Cache error during install:', error))
  );
  
  // تفعيل الـ Service Worker فوراً
  self.skipWaiting();
});

// تفعيل Service Worker
self.addEventListener('activate', event => {
  console.log('Service Worker Activating...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && 
              cacheName !== RUNTIME_CACHE && 
              cacheName !== API_CACHE) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  return self.clients.claim();
});

// اعتراض الطلبات
self.addEventListener('fetch', event => {
  const { request } = event;
  const { url, method } = request;

  // تجاهل طلبات POST/PUT/DELETE من التخزين المؤقت
  if (method !== 'GET') {
    return;
  }

  // التعامل مع طلبات API
  if (url.includes('/mobile/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // تخزين مؤقت للاستجابة الناجحة فقط
          if (response.status === 200) {
            const responseToCache = response.clone();
            caches.open(API_CACHE).then(cache => {
              cache.put(request, responseToCache);
            });
          }
          return response;
        })
        .catch(() => {
          // في حالة عدم الاتصال، محاولة جلب من التخزين المؤقت
          return caches.match(request)
            .then(response => {
              if (response) {
                return response;
              }
              // إذا لم يكن في التخزين المؤقت، إرجاع صفحة خطأ بدون إنترنت
              return new Response(
                JSON.stringify({
                  success: false,
                  message: 'بدون اتصال إنترنت',
                  offline: true
                }),
                {
                  status: 200,
                  statusText: 'Offline',
                  headers: new Headers({
                    'Content-Type': 'application/json'
                  })
                }
              );
            });
        })
    );
    return;
  }

  // استراتيجية Cache First للموارد الثابتة
  if (url.includes('/static/') || 
      url.includes('/images/') || 
      url.includes('/css/') || 
      url.includes('/js/')) {
    event.respondWith(
      caches.match(request)
        .then(response => {
          if (response) {
            return response;
          }
          return fetch(request)
            .then(response => {
              if (response.status !== 200) {
                return response;
              }
              const responseToCache = response.clone();
              caches.open(RUNTIME_CACHE).then(cache => {
                cache.put(request, responseToCache);
              });
              return response;
            });
        })
        .catch(() => {
          // إرجاع placeholder image إذا كان الطلب لصورة
          if (request.destination === 'image') {
            return new Response(
              '<svg></svg>',
              { headers: { 'Content-Type': 'image/svg+xml' } }
            );
          }
          return new Response('Offline');
        })
    );
    return;
  }

  // استراتيجية Network First للصفحات الديناميكية
  event.respondWith(
    fetch(request)
      .then(response => {
        // تخزين مؤقت للاستجابة الناجحة
        if (response.status === 200) {
          const responseToCache = response.clone();
          caches.open(RUNTIME_CACHE).then(cache => {
            cache.put(request, responseToCache);
          });
        }
        return response;
      })
      .catch(() => {
        // محاولة جلب من التخزين المؤقت
        return caches.match(request)
          .catch(() => {
            // إذا لم يكن في التخزين المؤقت، إرجاع صفحة بدون إنترنت
            return caches.match('/mobile/offline') ||
              new Response('Offline - الرجاء التحقق من الاتصال بالإنترنت');
          });
      })
  );
});

// معالجة الرسائل من العميل (Client)
self.addEventListener('message', event => {
  console.log('Message received in Service Worker:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    const urls = event.data.urls || [];
    caches.open(RUNTIME_CACHE).then(cache => {
      cache.addAll(urls).catch(error => {
        console.error('Error caching URLs:', error);
      });
    });
  }
});

// معالجة الرسائل في الخلفية
self.addEventListener('sync', event => {
  if (event.tag === 'sync-scans') {
    event.waitUntil(syncOfflineScans());
  }
});

/**
 * مزامنة البيانات المحفوظة محلياً (Scans) مع الخادم
 */
async function syncOfflineScans() {
  try {
    // فتح قاعدة البيانات المحلية
    const db = await openIndexedDB();
    const scans = await getOfflineScans(db);
    
    if (scans.length === 0) return;
    
    // إرسال البيانات إلى الخادم
    const response = await fetch('/mobile/api/sync/push', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        offline_data: scans
      })
    });
    
    if (response.ok) {
      // حذف البيانات المتزامنة
      await deleteOfflineScans(db, scans.map(s => s.id));
      
      // إرسال رسالة للعميل بالنجاح
      self.clients.matchAll().then(clients => {
        clients.forEach(client => {
          client.postMessage({
            type: 'SYNC_COMPLETE',
            success: true,
            syncedCount: scans.length
          });
        });
      });
    }
  } catch (error) {
    console.error('Error syncing offline scans:', error);
  }
}

function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('cfpa-zms-db', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('offlineScans')) {
        db.createObjectStore('offlineScans', { keyPath: 'id' });
      }
    };
  });
}

function getOfflineScans(db) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['offlineScans'], 'readonly');
    const store = transaction.objectStore('offlineScans');
    const request = store.getAll();
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

function deleteOfflineScans(db, ids) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['offlineScans'], 'readwrite');
    const store = transaction.objectStore('offlineScans');
    
    ids.forEach(id => {
      store.delete(id);
    });
    
    transaction.onerror = () => reject(transaction.error);
    transaction.oncomplete = () => resolve();
  });
}