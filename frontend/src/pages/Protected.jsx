import { useState, useEffect, useCallback } from 'react';
import { generateClient } from 'aws-amplify/api';
import { View, Heading, Flex, Alert, Button } from '@aws-amplify/ui-react';
import { getItems as GetItems } from '../graphql/queries';
import Plaid from '../components/Plaid';
import Institutions from '../components/Institutions';

export default function Protected() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);
  const getItems = useCallback(async () => {
    try {
      const client = generateClient();
      const all = [];
      let cursor;
      do {
        const res = await client.graphql({ query: GetItems, variables: { cursor } });
        all.push(...res.data.getItems.items);
        cursor = res.data.getItems.cursor;
      } while (cursor);
      setItems(all);
      setError(null);
    } catch {
      setError('Unable to load institutions. Please try again.');
    }
  }, []);
  useEffect(() => { getItems(); }, [getItems]);
  return (
    <Flex direction="column">
      <Plaid getItems={getItems}/>
      {error && <Alert variation="error">{error}<Button onClick={getItems}>Retry</Button></Alert>}
      <View><Heading>Institutions</Heading><Institutions institutions={items}/></View>
    </Flex>
  );
}
