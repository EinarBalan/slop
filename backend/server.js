const express = require('express');
const fs = require('fs');
const { parse } = require('csv-parse');
const path = require('path');
const cors = require('cors');

const app = express();
const port = 3000;

// Enable CORS for all routes
app.use(cors());

// Configuration
const BATCH_SIZE = 1000;
const CSV_FILE = path.join(__dirname, 'archive', 'outputRS_2022-11.csv');

// Helper function to check if a post is valid
function isValidPost(post) {
    return post.self_text && 
           post.self_text.trim() !== '' && 
           post.self_text !== '[deleted]' &&
           post.self_text !== '[removed]' &&
           post.over_18 !== 'true';
}

// Persistent stream and parser state
let fileStream = null;
let parser = null;
let isReadingBatch = false;
let batchIndex = 0;
let totalProcessedRows = 0;
let endOfFile = false;

// Initialize the stream and parser
function initializeStream() {
    if (fileStream) {
        fileStream.destroy();
    }
    
    fileStream = fs.createReadStream(CSV_FILE);
    parser = fileStream.pipe(parse({
        columns: true,
        skip_empty_lines: true
    }));
    
    // Set a higher max listeners limit
    parser.setMaxListeners(20);
    
    batchIndex = 0;
    totalProcessedRows = 0;
    endOfFile = false;
    
    console.log('CSV parser initialized');
}

// Initialize on server start
initializeStream();

// Function to read the next batch
async function readNextBatch() {
    // If we've reached the end of file, reset the stream
    if (endOfFile) {
        initializeStream();
    }
    
    // If we're already reading, wait
    if (isReadingBatch) {
        throw new Error('Already processing a batch');
    }
    
    isReadingBatch = true;
    
    return new Promise((resolve, reject) => {
        const batch = [];
        let skippedRows = 0;
        
        // Handle data events from where we left off
        function onData(row) {
            totalProcessedRows++;
            
            // If the batch is complete, pause and resolve
            if (batch.length >= BATCH_SIZE) {
                parser.pause();
                cleanup();
                
                console.log(`read batch ${batchIndex}`);

                isReadingBatch = false;
                resolve({ 
                    batch,
                    batchIndex: batchIndex++,
                    skippedRows,
                    totalProcessedRows
                });

                return;
            }
            
            // Add valid rows to our batch
            if (isValidPost(row)) {
                batch.push(row);
            } else {
                skippedRows++;
            }
        }
        
        // Handle the end of file
        function onEnd() {
            cleanup();
            
            endOfFile = true;
            isReadingBatch = false;
            
            resolve({ 
                batch, 
                batchIndex: batchIndex++, 
                skippedRows,
                totalProcessedRows,
                endOfFile: true
            });
        }
        
        // Handle errors
        function onError(error) {
            cleanup();
            
            isReadingBatch = false;
            reject(error);
        }

        // Cleanup function to remove all listeners
        function cleanup() {
            parser.removeListener('data', onData);
            parser.removeListener('end', onEnd);
            parser.removeListener('error', onError);
        }
        
        // Set up event listeners
        parser.on('data', onData);
        parser.on('end', onEnd);
        parser.on('error', onError);
        
        // Resume the parser if it's paused
        if (parser.isPaused()) {
            parser.resume();
        }
    });
}

// GET /batch endpoint - returns a batch of data and advances to the next batch
app.get('/batch', async (req, res) => {
    try {
        const result = await readNextBatch();
        
        // Send the response
        res.json({
            posts: result.batch,
            count: result.batch.length,
            batchIndex: result.batchIndex,
            skippedInvalidPosts: result.skippedRows,
            totalProcessedRows: result.totalProcessedRows,
            endOfFile: result.endOfFile || false,
            batchSize: BATCH_SIZE
        });
        
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

// GET /reset endpoint - resets the parser to the beginning of the file
app.get('/reset', (req, res) => {
    try {
        initializeStream();
        res.json({ message: 'Parser reset to beginning of file' });
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: 'Internal server error', message: error.message });
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
}); 