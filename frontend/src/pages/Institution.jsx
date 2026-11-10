import { useParams } from 'react-router-dom';
import { useState, useCallback } from 'react';
import { Divider, Flex, Heading, View, Button } from '@aws-amplify/ui-react';
import Refresh from '../components/Refresh';
import Accounts from '../components/Accounts';
import Transactions from '../components/Transactions';

export default function Institution() {

  const { id } = useParams();

  const [accountMap, setAccountMap] = useState({});

  const [refreshKey, setRefreshKey] = useState(0);

  const updateAccounts = useCallback((accounts) => {
    const accountMap = accounts.reduce((acc, cur, idx) => {
      acc[cur.account_id] = cur;
      return acc;
    }, {});
    setAccountMap(accountMap);
  }, []);

  return (
    <Flex direction="column">
      <Divider/>
      <Flex direction="row">
        <Heading level={5}>Institution</Heading>
        <Refresh item_id={id}/>
        <Button onClick={() => setRefreshKey(key => key + 1)}>Reload accounts and transactions</Button>
      </Flex>
      <Flex direction="row">
        <View>
          <Heading level={6}>Accounts</Heading>
          <Accounts key={`${id}-${refreshKey}`} id={id} updateAccounts={updateAccounts}/>
        </View>
        <View>
          <Heading level={6}>Transactions</Heading>
          <Transactions key={`${id}-${refreshKey}`} id={id} accounts={accountMap}/>
        </View>
      </Flex>
    </Flex>
  );
}
