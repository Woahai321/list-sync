# User Configuration End-to-End Test Plan

## Overview
This document provides a comprehensive test plan to verify the user configuration and assignment system works correctly across all components.

## Test Environment Setup

### Prerequisites
1. ListSync instance running (Frontend + Backend + Core)
2. Overseerr/Jellyseerr instance with at least 2 users configured
3. Access to database to verify data persistence

### Test Data
- **User 1 (Admin)**: ID = "1", display_name = "Admin User"
- **User 2 (Test)**: ID = "2", display_name = "Test User"
- **Test List**: IMDb Top 250 (`imdb:top`)

---

## Test Cases

### ✅ Test 1: Initial Setup Wizard - User Selection

**Objective:** Verify that users can select a default user during the setup wizard.

**Steps:**
1. Start fresh ListSync instance (or clear database)
2. Navigate to setup wizard at `http://localhost:3222/setup`
3. **Step 1 - Essential Configuration:**
   - Enter Overseerr URL
   - Enter Overseerr API Key
   - Click "Sync Users from Overseerr" button
4. Verify users are displayed in grid format
5. Select User 2 (Test User)
6. Verify "Selected User Summary" shows:
   - "Default User Selected" message
   - Selected user's display name
   - User ID

**Expected Results:**
- ✅ Users load successfully from Overseerr
- ✅ User cards display with avatars, names, emails, IDs
- ✅ Selected user is highlighted with purple border
- ✅ Summary box shows selected user information
- ✅ Can proceed to next step

**Verification Queries:**
```sql
-- Check config table for default user
SELECT key, value FROM config WHERE key = 'overseerr_user_id';
-- Expected: value = "2"

-- Check overseerr_users table populated
SELECT id, display_name, email FROM overseerr_users;
-- Expected: At least 2 users
```

---

### ✅ Test 2: Settings Page - Default User Display

**Objective:** Verify the Settings page correctly displays the default user.

**Steps:**
1. Navigate to `http://localhost:3222/settings`
2. Click on "Users" tab
3. Observe the "Default User for New Lists" section at the top

**Expected Results:**
- ✅ Default user box is displayed prominently
- ✅ Shows correct user (User 2 from Test 1)
- ✅ Displays user avatar, name, email, and ID
- ✅ Has blue/star icon indicating it's the default

**Verification:**
- Check that the displayed user matches the one selected in the wizard
- Verify the user ID matches the config value

---

### ✅ Test 3: Add List Modal - Default User Pre-population

**Objective:** Verify new lists default to the configured default user.

**Steps:**
1. Navigate to Lists page
2. Click "Add List" button
3. **Step 1:** Select "IMDb" as source
4. **Step 2:** Enter list ID: `top`
5. **Step 3:** Observe the "Request As User" section

**Expected Results:**
- ✅ User dropdown is pre-populated with User 2 (default from wizard)
- ✅ Shows green confirmation box: "This list will request content as: Test User"
- ✅ All Overseerr users are available in dropdown
- ✅ Can change user selection

**Verification:**
- Default user should match the one configured in wizard
- Dropdown should show all users from Overseerr

---

### ✅ Test 4: Add List with Custom User

**Objective:** Verify that lists can be assigned to different users.

**Steps:**
1. In Add List Modal (Step 3), change user from User 2 to User 1
2. Observe the green confirmation box updates
3. Click "Add List & Sync Now"
4. Wait for sync to complete

**Expected Results:**
- ✅ Confirmation box updates to show "Admin User"
- ✅ List is added successfully
- ✅ Sync completes without errors

**Verification Queries:**
```sql
-- Check list was saved with correct user_id
SELECT list_type, list_id, user_id FROM lists WHERE list_id = 'top';
-- Expected: user_id = "1"
```

---

### ✅ Test 5: Database Persistence

**Objective:** Verify user_id is correctly stored in the database.

**Steps:**
1. Add 3 lists with different users:
   - List A → User 1 (Admin)
   - List B → User 2 (Test User)
   - List C → User 1 (Admin)
2. Check database

**Expected Results:**
- ✅ Each list has correct `user_id` in database
- ✅ `user_id` matches the selected user at time of creation

**Verification Queries:**
```sql
-- Check all lists and their assigned users
SELECT 
    list_type,
    list_id,
    user_id,
    (SELECT display_name FROM overseerr_users WHERE id = lists.user_id) as user_name
FROM lists;

-- Expected output:
-- list_type | list_id | user_id | user_name
-- imdb      | top     | 1       | Admin User
-- trakt     | ...     | 2       | Test User
-- imdb      | ...     | 1       | Admin User
```

---

### ✅ Test 6: Sync Process - User ID Usage

**Objective:** Verify sync process uses the correct user_id when making requests.

**Steps:**
1. Enable debug logging in backend
2. Trigger sync for a list assigned to User 2
3. Monitor logs for:
   - User ID retrieval from database
   - OverseerrClient initialization
   - API request headers

**Expected Results:**
- ✅ Log shows: "Using user_id 2 from list configuration"
- ✅ OverseerrClient initialized with user_id = "2"
- ✅ HTTP requests include header: `X-Api-User: 2`

**Verification:**
Check backend logs for entries like:
```
INFO: Using user_id 2 from list configuration
INFO: Creating Overseerr client with user_id: 2
```

Check Overseerr request history:
- Requests should appear as made by "Test User", not "Admin User"

---

### ✅ Test 7: User Validation - Missing User Handling

**Objective:** Verify system handles deleted/missing users gracefully.

**Steps:**
1. Add a list with User 2
2. Delete User 2 from Overseerr (or change ID in database to non-existent user)
3. Trigger sync for that list
4. Monitor logs

**Expected Results:**
- ✅ Log shows warning: "User ID X not found in local user database"
- ✅ System attempts to validate against Overseerr API
- ✅ If user not found, falls back to User ID 1
- ✅ Sync continues without crashing

**Verification:**
Check logs for:
```
WARNING: User ID 2 not found in local user database
WARNING: User ID 2 not found in Overseerr. Falling back to default user ID 1
```

---

### ✅ Test 8: Settings Page - User Sync

**Objective:** Verify users can be synced from Overseerr via Settings.

**Steps:**
1. Add a new user in Overseerr (User 3)
2. Go to Settings → Users
3. Click "Sync Users" button
4. Observe user list updates

**Expected Results:**
- ✅ Sync button shows loading state
- ✅ New user (User 3) appears in the list
- ✅ "Last synced" timestamp updates
- ✅ Toast notification: "Users Synced - Successfully synced X users"

**Verification Queries:**
```sql
SELECT id, display_name, last_synced FROM overseerr_users ORDER BY id;
-- Expected: User 3 is now in the list
```

---

### ✅ Test 9: Add List Modal - No Users Warning

**Objective:** Verify warning appears when no users are available.

**Steps:**
1. Clear `overseerr_users` table manually (for testing):
   ```sql
   DELETE FROM overseerr_users;
   ```
2. Open Add List Modal
3. Navigate to Step 3

**Expected Results:**
- ✅ Dropdown is empty or shows fallback
- ✅ Warning box appears: "No users loaded. The default user (ID: 1) will be used."
- ✅ Suggestion to sync users from Settings

**Verification:**
- Warning should be amber/yellow colored
- Should link to Settings → Users page

---

### ✅ Test 10: Wizard User Selection - Display Names vs IDs

**Objective:** Verify users are displayed with names, not just IDs.

**Steps:**
1. Go through setup wizard
2. At user selection step, observe user cards

**Expected Results:**
- ✅ User cards show display names prominently
- ✅ User IDs shown as secondary info (badges)
- ✅ Email addresses shown if available
- ✅ Admin badge for User ID 1
- ✅ Avatars displayed (Overseerr or DiceBear fallback)

**Visual Check:**
- Should see "Admin User" not just "1"
- Should see "Test User" not just "2"

---

## Regression Tests

### RT1: Multiple Lists, Same User
Add 5 lists all assigned to User 2, verify all sync correctly.

### RT2: Container Restart Persistence
Add lists with various users, restart container, verify user_id persists.

### RT3: Concurrent Syncs
Sync 3 lists with different users simultaneously, verify no cross-contamination.

---

## Test Results Template

```markdown
## Test Execution Results

**Date:** YYYY-MM-DD
**Tester:** [Name]
**Environment:** [Development/Staging/Production]

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| Test 1  | Initial Setup Wizard | ✅ PASS | |
| Test 2  | Settings Default Display | ✅ PASS | |
| Test 3  | Add List Default User | ✅ PASS | |
| Test 4  | Add List Custom User | ✅ PASS | |
| Test 5  | Database Persistence | ✅ PASS | |
| Test 6  | Sync Process User ID | ✅ PASS | |
| Test 7  | Missing User Handling | ✅ PASS | |
| Test 8  | Settings User Sync | ✅ PASS | |
| Test 9  | No Users Warning | ✅ PASS | |
| Test 10 | Display Names vs IDs | ✅ PASS | |

### Issues Found
- None / [List issues]

### Overall Assessment
- ✅ All tests passed
- ⚠️ Minor issues found
- ❌ Critical issues found
```

---

## Quick Verification Script

```sql
-- Run this SQL script to verify user configuration is working

-- 1. Check default user in config
SELECT 'Default User Config' as check_name, value as user_id 
FROM config WHERE key = 'overseerr_user_id';

-- 2. Check users are synced
SELECT 'Synced Users' as check_name, COUNT(*) as count 
FROM overseerr_users;

-- 3. Check lists have user assignments
SELECT 
    'Lists with Users' as check_name,
    COUNT(*) as total_lists,
    COUNT(DISTINCT user_id) as unique_users
FROM lists;

-- 4. Show list-to-user mapping
SELECT 
    list_type,
    list_id,
    user_id,
    (SELECT display_name FROM overseerr_users WHERE id = lists.user_id) as user_name
FROM lists
ORDER BY user_id, list_type;

-- 5. Check for lists with missing users
SELECT 
    list_type,
    list_id,
    user_id
FROM lists
WHERE user_id NOT IN (SELECT id FROM overseerr_users)
    AND user_id != '1'; -- Exclude default admin
```

---

## Success Criteria

The user configuration system is working correctly if:

✅ **Setup Wizard:**
- Users can be synced and selected
- Default user is saved to config
- UI clearly shows selected user with name, not just ID

✅ **Add List Modal:**
- Defaults to configured user
- Shows user display name
- Allows changing per-list
- Shows confirmation of selected user

✅ **Settings Page:**
- Displays default user prominently
- Shows all synced users
- Can re-sync users from Overseerr

✅ **Database:**
- `lists.user_id` correctly stores assigned user
- `overseerr_users` table populated
- `config.overseerr_user_id` stores default

✅ **Sync Process:**
- Retrieves user_id from database
- Uses correct user in API calls
- Falls back gracefully if user missing
- Logs show correct user_id

✅ **User Experience:**
- Clear messaging about what "default user" means
- Visual confirmation of selected users
- Warnings when users are missing
- Easy to manage users in Settings

---

## Conclusion

This test plan covers all aspects of the user configuration system:
- Initial setup and defaults
- Per-list user assignment
- Database persistence
- Sync process execution
- Error handling and validation
- User interface clarity

Execute all tests in sequence to verify complete end-to-end functionality.






