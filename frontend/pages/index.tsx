import Head from 'next/head';
import { NextPage } from 'next';
import FileUpload from '../components/FileUpload';

const Home: NextPage = () => {
  return (
    <>
      <Head>
        <title>Budget App</title>
        <meta name="description" content="Upload your bank statements and categorize transactions" />
      </Head>
      <main style={{ padding: '2rem' }}>
        <h1>Budget Control</h1>
        <p>Upload your CSV or Excel files to parse and store your transactions.</p>
        <FileUpload />
      </main>
    </>
  );
};

export default Home;