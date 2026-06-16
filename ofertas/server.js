const express = require('express');
const cors = require('cors');
const { MongoClient } = require('mongodb');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// Configurações do seu MongoDB (defina em .env)
const MONGO_URL = process.env.MONGO_URL;
const MONGO_DB_NAME = process.env.MONGO_DB_NAME || "Oncinha";
const MONGO_COLLECTION_NAME = process.env.MONGO_COLLECTION_NAME || "ofertas_ia";

let mongoClient;

async function connectMongo() {
    try {
        if (!MONGO_URL) {
            throw new Error('MONGO_URL não está definida. Configure-a em .env');
        }
        mongoClient = new MongoClient(MONGO_URL);
        await mongoClient.connect();
        console.log('✅ Conectado ao MongoDB Atlas');
    } catch (err) {
        console.error('❌ Erro de conexão:', err);
    }
}

app.get('/api/frases/:id', async (req, res) => {
    try {
        const db = mongoClient.db(MONGO_DB_NAME);
        const collection = db.collection(MONGO_COLLECTION_NAME);
        const produtoId = parseInt(req.params.id);
        const doc = await collection.findOne({ produto_id: produtoId });
        
        if (doc && doc.frases) {
            res.json({ frases: doc.frases });
        } else {
            res.json({ frases: ["OUNCE STOCK", "OFERTA DO DIA"] });
        }
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log(`🚀 Servidor rodando em http://localhost:${PORT}`);
    connectMongo();
});