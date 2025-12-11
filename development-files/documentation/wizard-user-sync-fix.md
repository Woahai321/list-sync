# Setup Wizard User Sync Fix

## 🐛 Problem Identified

### Issue Description
During the setup wizard, when clicking "Sync Users from Overseerr", the following error occurred:

```
POST http://localhost:3222/api/overseerr/users/sync
Status: 400 Bad Request
Response: {"detail":"Overseerr URL and API key must be configured"}
```

### Root Cause Analysis

The issue occurred because:

1. **Test Connection** ✅ worked - It sends credentials in the request body:
   ```javascript
   POST /api/setup/test/overseerr
   {
     overseerr_url: "...",
     overseerr_api_key: "...",
     overseerr_user_id: "1"
   }
   ```

2. **Sync Users** ❌ failed - It expects credentials to already exist in the database:
   ```javascript
   POST /api/overseerr/users/sync
   // No body - reads from saved config
   ```

The `/api/overseerr/users/sync` endpoint tries to read `overseerr_url` and `overseerr_api_key` from the saved configuration, but during the setup wizard, these haven't been saved yet!

---

## ✅ Solution Implemented

### Fix Strategy

**Save credentials to database BEFORE trying to sync users.**

### Code Changes

**File:** `listsync-nuxt/components/setup/Step1Essential.vue`

**Function:** `testOverseerr()`

#### Before (Broken Flow):
```javascript
1. Test connection → Success ✅
2. Try to sync users → FAIL ❌ (no credentials in DB)
```

#### After (Fixed Flow):
```javascript
1. Test connection → Success ✅
2. Save credentials to database ✅
3. Sync users → Success ✅ (credentials now available)
```

### Implementation Details

```javascript
const testOverseerr = async () => {
  // ... validation code ...
  
  const result = await api.testOverseerrConnection({
    overseerr_url: url,
    overseerr_api_key: apiKey,
    overseerr_user_id: userId,
  })
  
  if (result.valid) {
    // ✨ NEW: Save credentials BEFORE syncing users
    await api.updateConfig({
      overseerr_url: url,
      overseerr_api_key: apiKey,
      overseerr_user_id: userId,
    })
    
    // Small delay to ensure database write completes
    await new Promise(resolve => setTimeout(resolve, 300))
    
    // NOW sync users - credentials are in database
    await fetchOverseerrUsers()
  }
}
```

### UI Improvements

**Updated Connection Status Message:**
```vue
<p v-else-if="overseerrValidated" class="text-xs text-green-400/80">
  ✅ Connected & Credentials Saved
</p>
```

This clearly indicates that:
1. Connection was successful
2. Credentials have been saved to the database
3. Ready to sync users

---

## 🔄 Updated Flow

### Complete Setup Wizard Flow

```
1. USER ENTERS CREDENTIALS
   ├── URL: https://overseerr.example.com
   └── API Key: *********************

2. USER CLICKS "Sync Users from Overseerr"
   │
   ├─→ 3. TEST CONNECTION
   │   POST /api/setup/test/overseerr
   │   ├── Send credentials in request
   │   └── Response: 200 OK ✅
   │
   ├─→ 4. SAVE CREDENTIALS (NEW STEP!)
   │   POST /api/config
   │   ├── Save to database
   │   └── Show "Connected & Credentials Saved" ✅
   │
   └─→ 5. SYNC USERS
       POST /api/overseerr/users/sync
       ├── Read credentials from database ✅
       ├── Fetch users from Overseerr
       ├── Save users to overseerr_users table
       └── Display user cards ✅
```

---

## 📊 API Endpoints Involved

### 1. Test Connection
```http
POST /api/setup/test/overseerr
Content-Type: application/json

{
  "overseerr_url": "https://overseerr.example.com",
  "overseerr_api_key": "abc123",
  "overseerr_user_id": "1"
}

Response: 200 OK
{
  "valid": true,
  "message": "Overseerr connection successful",
  "version": "2.7.3",
  "user": { ... }
}
```

### 2. Save Configuration (NEW CALL)
```http
POST /api/config
Content-Type: application/json

{
  "overseerr_url": "https://overseerr.example.com",
  "overseerr_api_key": "abc123",
  "overseerr_user_id": "1"
}

Response: 200 OK
{
  "success": true,
  "message": "Configuration updated"
}
```

### 3. Sync Users
```http
POST /api/overseerr/users/sync
Content-Type: application/json
(No body - reads from saved config)

Response: 200 OK
{
  "success": true,
  "users": [
    {
      "id": "1",
      "display_name": "Admin",
      "email": "admin@example.com",
      "avatar": "/path/to/avatar"
    }
  ],
  "count": 3
}
```

---

## 🎯 What This Fixes

### Before Fix
❌ "Sync Users from Overseerr" button fails silently or with cryptic error  
❌ Users can't complete setup wizard  
❌ Credentials not saved until Step 2  

### After Fix
✅ Credentials saved immediately after successful connection  
✅ User sync works reliably  
✅ Clear feedback: "Connected & Credentials Saved"  
✅ Users can complete wizard successfully  

---

## 🧪 Testing

### Manual Test Steps

1. **Start fresh setup wizard**
   ```
   Navigate to: http://localhost:3222/setup
   ```

2. **Enter credentials**
   - URL: `https://your-overseerr.com`
   - API Key: `your-api-key`

3. **Click "Sync Users from Overseerr"**

4. **Verify success**
   - ✅ See "Connected & Credentials Saved"
   - ✅ User cards appear
   - ✅ No 400 error in network tab

### Expected Console Output
```
Testing Overseerr with URL: https://... API Key: ***
Saving credentials to config before syncing users...
Credentials saved to config successfully
Overseerr validation successful, now fetching users...
Fetching Overseerr users...
Fetched 3 users: [...]
```

### Database Verification
```sql
-- Check credentials were saved
SELECT key, value FROM config 
WHERE key IN ('overseerr_url', 'overseerr_api_key', 'overseerr_user_id');

-- Check users were synced
SELECT id, display_name, email FROM overseerr_users;
```

---

## 🔐 Security Considerations

### Credential Handling
- ✅ API keys are masked in UI (shown as •••)
- ✅ API keys are masked in console logs (shown as ***)
- ✅ Credentials are sent over HTTPS in production
- ✅ Credentials are stored securely in database

### Early Credential Storage
**Q:** Is it safe to save credentials before completing the wizard?

**A:** Yes, because:
1. Credentials are validated before saving (test connection succeeds)
2. User can complete or cancel wizard - credentials remain valid
3. If user abandons setup, next visit will use saved credentials
4. No security risk - credentials are required for any operation anyway

---

## 📝 Additional Changes Made

### 1. Button Enable/Disable Logic
**Before:** Button disabled until fields filled  
**After:** Button always enabled, shows helpful error if fields empty

### 2. Error Messages
**Before:** Generic "Missing Information"  
**After:** Specific "Please enter: Overseerr URL and API Key"

### 3. Console Logging
Added comprehensive logging for debugging:
- Connection test status
- Credential save status
- User sync status

---

## 🚀 Future Enhancements

### Potential Improvements

1. **Retry Logic**
   - Add automatic retry for transient failures
   - Show retry count to user

2. **Partial Success Handling**
   - If credential save fails but connection succeeds
   - Show warning and allow retry

3. **Progress Indicators**
   - Show step-by-step progress:
     - Testing connection...
     - Saving credentials...
     - Syncing users...

4. **Offline Mode**
   - Cache users for offline wizard completion
   - Sync when connection restored

---

## 📚 Related Documentation

- **Test Plan:** `development-files/testing/user-config-test-plan.md`
- **Implementation Summary:** `development-files/documentation/user-config-implementation-summary.md`
- **User Configuration Plan:** `user-co.plan.md`

---

## ✅ Verification Checklist

- [x] Credentials are saved before user sync
- [x] User sync endpoint receives valid credentials
- [x] "Connected & Credentials Saved" message displays
- [x] User cards display after successful sync
- [x] No 400 errors in network tab
- [x] Console logs show successful flow
- [x] Database contains saved credentials
- [x] Database contains synced users

---

**Status:** ✅ Fixed  
**Date:** December 6, 2025  
**Version:** v0.7.0-dev  
**Impact:** Critical - Blocks setup wizard completion






