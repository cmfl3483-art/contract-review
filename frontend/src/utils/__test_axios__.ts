/**
 * Test file to verify Axios configuration
 * This file can be deleted after verification
 */

import { get, post, upload, download } from './request';
import { API_ENDPOINTS } from '../config/api';

// Example usage of the configured Axios client

// GET request example
export async function testGetContracts() {
  try {
    const data = await get(API_ENDPOINTS.CONTRACTS.LIST);
    console.log('Contracts:', data);
    return data;
  } catch (error) {
    console.error('Error fetching contracts:', error);
    throw error;
  }
}

// POST request example
export async function testCreateContract() {
  try {
    const data = await post(API_ENDPOINTS.CONTRACTS.CREATE, {
      name: 'Test Contract',
      description: 'Test Description',
      reviewers: ['user1', 'user2'],
      ccUsers: ['user3'],
    });
    console.log('Created contract:', data);
    return data;
  } catch (error) {
    console.error('Error creating contract:', error);
    throw error;
  }
}

// Upload file example
export async function testUploadFile(contractId: string, file: File) {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const data = await upload(
      API_ENDPOINTS.CONTRACTS.ATTACHMENTS(contractId),
      formData,
      (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / (progressEvent.total || 1)
        );
        console.log(`Upload progress: ${percentCompleted}%`);
      }
    );
    console.log('Uploaded file:', data);
    return data;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
}

// Download file example
export async function testDownloadFile(attachmentId: string, filename: string) {
  try {
    await download(API_ENDPOINTS.ATTACHMENTS.DOWNLOAD(attachmentId), filename);
    console.log('File downloaded successfully');
  } catch (error) {
    console.error('Error downloading file:', error);
    throw error;
  }
}
