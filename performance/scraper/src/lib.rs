use pyo3::prelude::*;

mod trie;
use trie::_Trie;

mod webscrap;

#[pymodule]
fn scraper(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<_Trie>()?;
    Ok(())
}
