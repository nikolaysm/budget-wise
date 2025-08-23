import React from 'react';
import Head from 'next/head';

interface LayoutProps {
  title?: string;
  children: React.ReactNode;
}

/**
 * Simple layout component providing a document head and consistent padding.
 */
const Layout: React.FC<LayoutProps> = ({ title, children }) => {
  return (
    <>
      <Head>
        <title>{title ?? 'Budget App'}</title>
      </Head>
      <div style={{ maxWidth: '800px', margin: '0 auto', padding: '1rem' }}>{children}</div>
    </>
  );
};

export default Layout;