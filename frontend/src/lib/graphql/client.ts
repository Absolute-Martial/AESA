import { ApolloClient, InMemoryCache, HttpLink, split, ApolloLink } from '@apollo/client';
import { getMainDefinition } from '@apollo/client/utilities';

// API URL from environment or default
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const GRAPHQL_URL = `${API_URL}/graphql`;

// HTTP Link for queries and mutations
const httpLink = new HttpLink({
  uri: GRAPHQL_URL,
  credentials: 'include',
});

// Error handling link
const errorLink = new ApolloLink((operation, forward) => {
  return forward(operation).map((response) => {
    if (response.errors) {
      console.error('[GraphQL Errors]:', response.errors);
    }
    return response;
  });
});

// Cache configuration with type policies
const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        // Merge tasks by ID
        tasks: {
          keyArgs: ['filter'],
          merge(existing = [], incoming) {
            return incoming;
          },
        },
        // Cache today's schedule
        todaySchedule: {
          merge: true,
        },
        // Cache goals
        goals: {
          keyArgs: ['status'],
          merge(existing = [], incoming) {
            return incoming;
          },
        },
        // Cache notifications
        notifications: {
          keyArgs: ['unreadOnly'],
          merge(existing = [], incoming) {
            return incoming;
          },
        },
      },
    },
    Task: {
      keyFields: ['id'],
    },
    TimeBlock: {
      keyFields: ['id'],
    },
    Subject: {
      keyFields: ['id'],
    },
    Goal: {
      keyFields: ['id'],
    },
    Notification: {
      keyFields: ['id'],
    },
    StudySession: {
      keyFields: ['id'],
    },
  },
});

// Create Apollo Client
export const apolloClient = new ApolloClient({
  link: ApolloLink.from([errorLink, httpLink]),
  cache,
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
    },
    query: {
      fetchPolicy: 'cache-first',
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
  devtools: {
    enabled: process.env.NODE_ENV === 'development',
  },
});

// Helper to reset cache (useful for logout)
export const resetApolloCache = () => {
  return apolloClient.resetStore();
};
