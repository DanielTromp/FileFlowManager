/**
 * Native macOS Notifications (T158)
 *
 * Provides utility functions for sending native system notifications
 * when file operations complete.
 */

import { isPermissionGranted, requestPermission, sendNotification } from '@tauri-apps/api/notification';

let permissionGranted = false;

/**
 * Request notification permission on app startup
 */
export async function initializeNotifications(): Promise<boolean> {
  if (typeof window === 'undefined') return false;

  try {
    // Check if permission is already granted
    permissionGranted = await isPermissionGranted();

    // If not, request permission
    if (!permissionGranted) {
      const permission = await requestPermission();
      permissionGranted = permission === 'granted';
    }

    return permissionGranted;
  } catch (error) {
    console.error('Failed to initialize notifications:', error);
    return false;
  }
}

/**
 * Send notification for dry run scan completion
 */
export async function notifyScanComplete(filesMatched: number, operationsPlanned: number): Promise<void> {
  if (typeof window === 'undefined' || !permissionGranted) return;

  try {
    await sendNotification({
      title: 'FileFlow: Scan Complete',
      body: `Found ${filesMatched} files matching rules. ${operationsPlanned} operations planned.`,
      icon: 'icons/icon.png',
    });
  } catch (error) {
    console.error('Failed to send scan notification:', error);
  }
}

/**
 * Send notification for operation execution completion
 */
export async function notifyExecutionComplete(
  successCount: number,
  failedCount: number,
  spaceFree: number
): Promise<void> {
  if (typeof window === 'undefined' || !permissionGranted) return;

  try {
    const title = failedCount > 0
      ? 'FileFlow: Execution Completed with Errors'
      : 'FileFlow: Execution Complete';

    const body = failedCount > 0
      ? `✓ ${successCount} succeeded, ✗ ${failedCount} failed. ${spaceFree.toFixed(1)} MB freed.`
      : `✓ ${successCount} operations completed successfully. ${spaceFree.toFixed(1)} MB freed.`;

    await sendNotification({
      title,
      body,
      icon: 'icons/icon.png',
    });
  } catch (error) {
    console.error('Failed to send execution notification:', error);
  }
}

/**
 * Send notification for file deletion operations
 */
export async function notifyDeletionComplete(deletedCount: number, spaceFree: number): Promise<void> {
  if (typeof window === 'undefined' || !permissionGranted) return;

  try {
    await sendNotification({
      title: 'FileFlow: Deletion Complete',
      body: `Deleted ${deletedCount} files, freed ${spaceFree.toFixed(1)} MB.`,
      icon: 'icons/icon.png',
    });
  } catch (error) {
    console.error('Failed to send deletion notification:', error);
  }
}

/**
 * Send notification for rule updates
 */
export async function notifyRuleUpdated(ruleName: string, enabled: boolean): Promise<void> {
  if (typeof window === 'undefined' || !permissionGranted) return;

  try {
    await sendNotification({
      title: 'FileFlow: Rule Updated',
      body: `"${ruleName}" is now ${enabled ? 'enabled' : 'disabled'}.`,
      icon: 'icons/icon.png',
    });
  } catch (error) {
    console.error('Failed to send rule notification:', error);
  }
}

/**
 * Check if notifications are enabled
 */
export function areNotificationsEnabled(): boolean {
  return permissionGranted;
}
