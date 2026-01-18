use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ProjectNode {
    pub id: Uuid,
    pub name: String,
    pub kind: String,
    // #[serde(skip)]
    pub data: Vec<u8>,
    pub children: Vec<ProjectNode>,
}

impl ProjectNode {
    pub fn new(name: &str, kind: &str) -> Self {
        Self {
            id: Uuid::now_v7(),
            name: name.to_string(),
            kind: kind.to_string(),
            data: Vec::new(),
            children: Vec::new(),
        }
    }

    pub fn add_child(&mut self, child: ProjectNode) {
        self.children.push(child)
    }

    pub fn find_by_id(&self, id: &Uuid) -> Option<&ProjectNode> {
        if &self.id == id {
            return Some(self);
        }

        for child in &self.children {
            if let Some(found) = child.find_by_id(id) {
                return Some(found);
            }
        }

        None
    }

    pub fn find_by_id_mut(&mut self, id: &Uuid) -> Option<&mut ProjectNode> {
        if &self.id == id {
            return Some(self);
        }

        for child in &mut self.children {
            if let Some(found) = child.find_by_id_mut(id) {
                return Some(found);
            }
        }

        None
    }
}

/// Raw node structure for deserializing plugin output (without id)
#[derive(Debug, Deserialize)]
pub struct RawProjectNode {
    pub name: String,
    pub kind: String,
    pub data: Vec<u8>,
    #[serde(default)]
    pub children: Vec<RawProjectNode>,
}

impl From<RawProjectNode> for ProjectNode {
    fn from(raw: RawProjectNode) -> Self {
        Self {
            id: Uuid::now_v7(),
            name: raw.name,
            kind: raw.kind,
            data: raw.data,
            children: raw.children.into_iter().map(ProjectNode::from).collect(),
        }
    }
}

pub struct Project {
    pub root_node: ProjectNode,
    pub is_temporary: bool,
}

impl Project {
    pub fn new(is_temporary: bool) -> Self {
        let root_node = ProjectNode::new("root", "none");

        Self {
            root_node: root_node,
            is_temporary,
        }
    }
}
