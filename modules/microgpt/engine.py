
import json
import math
import random
import urllib.request

from core.config import PROJECT_ROOT
from core.logger import get_logger

log = get_logger("microgpt.engine")

class Value:
    """
    Stores a single scalar value and its gradient.
    """
    # __slots__ = ('data', 'grad', '_children', '_op', 'label')

    def __init__(self, data, _children=(), _op='', label=''):
        self.data = data
        self.grad = 0
        self._children = set(_children)
        self._op = _op
        self.label = label

    def __repr__(self):
        return f"Value(data={self.data}, grad={self.grad})"

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), '+')
        
        def _backward():
            self.grad += out.grad
            other.grad += out.grad
        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), '*')
        
        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out

    def __pow__(self, other):
        assert isinstance(other, (int, float)), "only supporting int/float powers for now"
        out = Value(self.data**other, (self,), f'**{other}')

        def _backward():
            self.grad += (other * self.data**(other-1)) * out.grad
        out._backward = _backward
        return out

    def exp(self):
        x = self.data
        out = Value(math.exp(x), (self,), 'exp')
        
        def _backward():
            self.grad += out.data * out.grad
        out._backward = _backward
        return out

    def log(self):
        x = self.data
        out = Value(math.log(x), (self,), 'log')

        def _backward():
            self.grad += (1/x) * out.grad
        out._backward = _backward
        return out

    def relu(self):
        out = Value(0 if self.data < 0 else self.data, (self,), 'ReLU')

        def _backward():
            self.grad += (out.data > 0) * out.grad
        out._backward = _backward
        return out

    def backward(self):
        # topological order all of the children in the graph
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._children:
                    build_topo(child)
                topo.append(v)
        build_topo(self)

        self.grad = 1
        for v in reversed(topo):
            if hasattr(v, '_backward'):
                v._backward()

    def __neg__(self): # -self
        return self * -1

    def __radd__(self, other): # other + self
        return self + other

    def __sub__(self, other): # self - other
        return self + (-other)

    def __rsub__(self, other): # other - self
        return other + (-self)

    def __rmul__(self, other): # other * self
        return self * other

    def __truediv__(self, other): # self / other
        return self * other**-1
    
    def __rtruediv__(self, other): # other / self
        return other * self**-1


class MicroGPTVisualizer:
    def __init__(self):
        self.data_dir = PROJECT_ROOT / "data" / "microgpt"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.trace_file = self.data_dir / "trace.json"
        self.input_file = self.data_dir / "input.txt"
        
        # Hyperparameters
        self.n_layer = 1
        self.n_embd = 16
        self.block_size = 16
        self.n_head = 4
        self.head_dim = self.n_embd // self.n_head
        self.learning_rate = 0.01
        self.num_steps = 50  # Reduced for quick demo, but enough to show learning curve
        
        self._prepare_data()
        self._init_model()

    def _prepare_data(self):
        # Similar to original code but uses established paths
        if not self.input_file.exists():
            log.info("Downloading input.txt...")
            names_url = 'https://raw.githubusercontent.com/karpathy/makemore/988aa59/names.txt'
            try:
                urllib.request.urlretrieve(names_url, str(self.input_file))
            except Exception as e:
                log.error(f"Failed to download input.txt: {e}")
                # Fallback to dummy data if download fails
                with open(self.input_file, 'w') as f:
                    f.write("emma\nolivia\nava\nisabella\nsophia\n")
        
        self.docs = [line.strip() for line in open(self.input_file, 'r', encoding='utf-8') if line.strip()]
        random.seed(42)
        random.shuffle(self.docs)
        
        self.uchars = sorted(set(''.join(self.docs)))
        self.vocab_size = len(self.uchars) + 1 # +1 for BOS
        self.BOS = len(self.uchars)
        self.stoi = {ch:i for i,ch in enumerate(self.uchars)}
        self.itos = {i:ch for i,ch in enumerate(self.uchars)}
        self.itos[self.BOS] = '.' # Visual representation for BOS/EOS

    def _init_model(self):
        # Helper to create matrix of Values
        def matrix(nout, nin, std=0.08):
            return [[Value(random.gauss(0, std)) for _ in range(nin)] for _ in range(nout)]

        self.state_dict = {
            'wte': matrix(self.vocab_size, self.n_embd),
            'wpe': matrix(self.block_size, self.n_embd),
            'lm_head': matrix(self.vocab_size, self.n_embd)
        }
        
        for i in range(self.n_layer):
            self.state_dict[f'layer{i}.attn_wq'] = matrix(self.n_embd, self.n_embd)
            self.state_dict[f'layer{i}.attn_wk'] = matrix(self.n_embd, self.n_embd)
            self.state_dict[f'layer{i}.attn_wv'] = matrix(self.n_embd, self.n_embd)
            self.state_dict[f'layer{i}.attn_wo'] = matrix(self.n_embd, self.n_embd)
            self.state_dict[f'layer{i}.mlp_fc1'] = matrix(4 * self.n_embd, self.n_embd)
            self.state_dict[f'layer{i}.mlp_fc2'] = matrix(self.n_embd, 4 * self.n_embd)
            
        self.params = [p for mat in self.state_dict.values() for row in mat for p in row]
        
        # Optimizer buffers
        self.m = [0.0] * len(self.params)
        self.v = [0.0] * len(self.params)

    # --- Model Functions (Methods) ---
    
    def linear(self, x, w):
        return [sum((wi * xi for wi, xi in zip(wo, x)), Value(0)) for wo in w]

    def softmax(self, logits):
        # max_val for stability (optional in pure math but good practice)
        # Using simple exp here for direct Value graph
        counts = [logit.exp() for logit in logits]
        denominator = sum(counts, Value(0))
        out = [c / denominator for c in counts]
        return out

    def rmsnorm(self, x):
        ms = sum((xi * xi for xi in x), Value(0)) / len(x)
        # Add small epsilon to avoid division by zero
        scale = (ms + 1e-5)**-0.5 
        return [xi * scale for xi in x]

    def gpt(self, token_id, pos_id, keys, values):
        # Embeddings
        tok_emb = self.state_dict['wte'][token_id]
        pos_emb = self.state_dict['wpe'][pos_id]
        x = [t + p for t, p in zip(tok_emb, pos_emb)]
        
        # Norm
        x = self.rmsnorm(x)

        for li in range(self.n_layer):
            # Attention
            x_residual = x
            x = self.rmsnorm(x)
            
            q = self.linear(x, self.state_dict[f'layer{li}.attn_wq'])
            k = self.linear(x, self.state_dict[f'layer{li}.attn_wk'])
            v = self.linear(x, self.state_dict[f'layer{li}.attn_wv'])
            
            keys[li].append(k)
            values[li].append(v)
            
            x_attn = []
            for h in range(self.n_head):
                hs = h * self.head_dim
                q_h = q[hs : hs + self.head_dim]
                
                # Causal attention: attend to past keys
                # Flatten head logic slightly for clarity
                k_h_past = [ki[hs : hs + self.head_dim] for ki in keys[li]]
                v_h_past = [vi[hs : hs + self.head_dim] for vi in values[li]]
                
                # Attention scores
                # (query . key) / sqrt(dim)
                scale = self.head_dim ** -0.5
                attn_logits = []
                for t, k_vec in enumerate(k_h_past):
                    dot = sum((q_h[j] * k_vec[j] for j in range(self.head_dim)), Value(0))
                    attn_logits.append(dot * scale)
                
                attn_weights = self.softmax(attn_logits)
                
                # Weighted sum of values
                head_out = []
                for j in range(self.head_dim):
                    # sum(weight[t] * val[t][j])
                    val = sum((attn_weights[t] * v_h_past[t][j] for t in range(len(v_h_past))), Value(0))
                    head_out.append(val)
                x_attn.extend(head_out)
            
            # Projection
            x = self.linear(x_attn, self.state_dict[f'layer{li}.attn_wo'])
            x = [a + b for a, b in zip(x, x_residual)]
            
            # MLP
            x_residual = x
            x = self.rmsnorm(x)
            x = self.linear(x, self.state_dict[f'layer{li}.mlp_fc1'])
            x = [xi.relu() for xi in x]
            x = self.linear(x, self.state_dict[f'layer{li}.mlp_fc2'])
            x = [a + b for a, b in zip(x, x_residual)]

        logits = self.linear(x, self.state_dict['lm_head'])
        return logits

    def trace_graph(self, root):
        nodes, edges = set(), set()
        def build(v):
            if v not in nodes:
                nodes.add(v)
                for child in v._children:
                    edges.add((child, v))
                    build(child)
        build(root)
        return nodes, edges

    def export_graph(self, root):
        """Differs from trace_graph by returning JSON-serializable structure"""
        # Limit depth or nodes to avoid massive JSON
        # For visualization, we might only want the immediate calculation of the loss for the last token
        
        _nodes, _edges = set(), set()
        
        # DFS with depth limit
        visited = set()
        
        node_list = []
        edge_list = []
        
        # Assign IDs
        uid = 0
        id_map = {}
        
        def get_id(v):
            nonlocal uid
            if v not in id_map:
                id_map[v] = uid
                uid += 1
            return id_map[v]

        def walk(v, depth):
            if v in visited:
                return
            visited.add(v)
            if depth > 10: # Only go 10 layers deep for visual sanity
                 return
            
            node_id = get_id(v)
            label = f"{v.data:.4f}"
            if v._op:
                label = f"{v._op} | " + label
            
            node_list.append({
                "id": node_id,
                "label": label,
                "op": v._op,
                "data": v.data,
                "grad": v.grad
            })
            
            for child in v._children:
                walk(child, depth + 1)
                child_id = get_id(child)
                edge_list.append({"from": child_id, "to": node_id})
        
        walk(root, 0)
        return {"nodes": node_list, "edges": edge_list}

    def run(self):
        log.info("Starting MicroGPT training...")
        
        losses = []
        
        beta1, beta2, eps_adam = 0.85, 0.99, 1e-8
        
        # Training Loop
        for step in range(self.num_steps):
            doc = self.docs[step % len(self.docs)]
            # Tokenize: BOS + chars + BOS
            tokens = [self.BOS] + [self.uchars.index(ch) for ch in doc] + [self.BOS]
            n = min(self.block_size, len(tokens) - 1)
            
            keys, values = [[] for _ in range(self.n_layer)], [[] for _ in range(self.n_layer)]
            step_losses = []
            
            # Forward pass per token
            for pos_id in range(n):
                token_id, target_id = tokens[pos_id], tokens[pos_id + 1]
                logits = self.gpt(token_id, pos_id, keys, values)
                probs = self.softmax(logits)
                loss_t = -probs[target_id].log()
                step_losses.append(loss_t)
            
            loss = sum(step_losses, Value(0)) * (1.0 / n)
            
            # Backward
            self.zero_grad() 
            loss.backward()
            
            # Optimizer Step
            lr_t = self.learning_rate * (1 - step / self.num_steps)
            for i, p in enumerate(self.params):
                self.m[i] = beta1 * self.m[i] + (1 - beta1) * p.grad
                self.v[i] = beta2 * self.v[i] + (1 - beta2) * p.grad ** 2
                m_hat = self.m[i] / (1 - beta1 ** (step + 1))
                v_hat = self.v[i] / (1 - beta2 ** (step + 1))
                p.data -= lr_t * m_hat / (v_hat ** 0.5 + eps_adam)
            
            losses.append({'step': step + 1, 'loss': loss.data})
            if (step + 1) % 10 == 0:
                log.info(f"Step {step+1}/{self.num_steps} | Loss: {loss.data:.4f}")

        # Capture Generation
        log.info("Generating samples...")
        samples = []
        temperature = 0.8
        for _ in range(5):
            keys, values = [[] for _ in range(self.n_layer)], [[] for _ in range(self.n_layer)]
            token_id = self.BOS
            sample_tokens = []
            for pos_id in range(self.block_size):
                logits = self.gpt(token_id, pos_id, keys, values)
                probs = self.softmax([logit * (1.0 / temperature) for logit in logits])
                
                # Sample
                p_data = [p.data for p in probs]
                token_id = random.choices(range(self.vocab_size), weights=p_data)[0]
                
                if token_id == self.BOS:
                    break
                sample_tokens.append(self.itos.get(token_id, '?'))
            
            samples.append("".join(sample_tokens))

        # Capture Graph (of the last training step's loss)
        # We need to serialize a small part of the graph, or the whole thing is too huge.
        # Let's verify if 'loss' is still valid from the loop
        graph_data = self.export_graph(loss) 
        
        trace = {
            'final_loss': loss.data,
            'loss_history': losses,
            'samples': samples,
            'vocab': self.uchars,
            'graph': graph_data,
            'params': {
                'n_layer': self.n_layer,
                'n_embd': self.n_embd,
                'n_head': self.n_head,
                'block_size': self.block_size
            }
        }
        
        with open(self.trace_file, 'w', encoding='utf-8') as f:
            json.dump(trace, f, indent=2)
            
        log.info(f"Trace saved to {self.trace_file}")
        return trace

    def zero_grad(self):
        for p in self.params:
            p.grad = 0

if __name__ == '__main__':
    viz = MicroGPTVisualizer()
    viz.run()
