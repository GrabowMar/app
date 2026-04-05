import type { Handle, HandleServerError } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
    const response = await resolve(event);
    return response;
};

export const handleError: HandleServerError = async ({ error }) => {
    console.error('Server error:', error);
    return {
        message: 'An unexpected error occurred',
    };
};
