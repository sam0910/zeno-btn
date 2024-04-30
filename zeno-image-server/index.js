// Requiring module
const express = require('express');
const cors = require('cors')
// Creating express object
const app = express();
app.use(cors());
// Defining port number
const PORT = 3000;

// Function to serve all static files
// inside public directory.
app.use(express.static('public'));
app.use('/images', express.static('images'));

// Server setup
app.listen(PORT, () => {
    console.log(`Running server on PORT ${PORT}...`);
})