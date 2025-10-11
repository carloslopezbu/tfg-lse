use pyo3::prelude::*;
mod trie;

use trie::_Trie;

#[pymodule]
fn rust_wordsoup(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<_Trie>()?;
    Ok(())
}
