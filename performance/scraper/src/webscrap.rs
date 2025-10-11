use serde::{Deserialize, Serialize};
use serde_json::Result;

#[derive(Serialize, Deserialize)]
struct STSData {
    href: String,
    text: String,
    word_type: String,
    video: String,
    categorie: String,
}
