import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, Button, FlatList } from 'react-native';

export default function App() {
  const [listings, setListings] = useState([]);
  const [title, setTitle] = useState('');
  const [price, setPrice] = useState('');

  const addListing = () => {
    if (!title.trim()) return;
    setListings([...listings, { id: Date.now().toString(), title, price }]);
    setTitle('');
    setPrice('');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Real Estate Listings</Text>

      <View style={styles.form}>
        <TextInput
          style={styles.input}
          placeholder="Property title"
          value={title}
          onChangeText={setTitle}
        />
        <TextInput
          style={styles.input}
          placeholder="Price"
          value={price}
          onChangeText={setPrice}
        />
        <Button title="Add Listing" onPress={addListing} />
      </View>

      <FlatList
        data={listings}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{item.title}</Text>
            <Text>{item.price}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  heading: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
  form: { marginBottom: 20 },
  input: { borderWidth: 1, borderColor: '#ccc', marginBottom: 10, padding: 8 },
  card: { padding: 15, backgroundColor: '#f8f8f8', marginBottom: 10 },
  cardTitle: { fontWeight: 'bold' }
});
