import gzip
import json
import zipfile

class ResultLoader(object):
  def __init__(self, tree_summary_fn, mutation_list_fn, mutation_assignment_fn):
    self._tree_summary_fn = tree_summary_fn
    self._mutation_list_fn = mutation_list_fn
    self._mutation_assignment_fn = mutation_assignment_fn

    self.mutlist = None
    self.tree_summary = None
    self.dataset_name = None

    self._load_tree_data()

  def _convert_keys_to_ints(self, dic):
    keys = dic.keys()
    for key in dic.keys():
      dic[int(key)] = dic[key]
      del dic[key]

  def _load_tree_data(self):
    with gzip.GzipFile(self._tree_summary_fn) as treesummf:
      tree_json = json.load(treesummf)
      self.dataset_name = tree_json['dataset_name']
      self.tree_summary = tree_json['trees']

    self._convert_keys_to_ints(self.tree_summary)
    for tree_idx, tree_features in self.tree_summary.items():
      self._convert_keys_to_ints(tree_features['populations'])
      self._convert_keys_to_ints(tree_features['structure'])

    with gzip.GzipFile(self._mutation_list_fn) as mutlistf:
      self.mutlist = json.load(mutlistf)
    self.num_ssms = len(self.mutlist['ssms'])

  def _load_assignments(self, mutf, tree_idx):
    mutass = json.loads(mutf.read('%s.json' % tree_idx))
    mutass = mutass['mut_assignments']
    self._convert_keys_to_ints(mutass)
    return mutass

  def load_mut_assignments(self, tree_idx):
    with zipfile.ZipFile(self._mutation_assignment_fn) as mutf:
      return self._load_assignments(mutf, tree_idx)

  def load_all_mut_assignments(self):
    with zipfile.ZipFile(self._mutation_assignment_fn) as mutf:
      for zinfo in mutf.infolist():
        tree_idx = int(zinfo.filename.split('.')[0])
        yield (tree_idx, self._load_assignments(mutf, tree_idx))

  def get_ssm_names(mutass):
    def _ssm_key(name):
      chrom, pos = name.split('_')
      chrom = chrom.lower()
      pos = int(pos)

      if chrom == 'x':
        chrom = 100
      elif chrom == 'y':
        chrom = 101
      else:
        chrom = int(chrom)
      return (chrom, pos)

    _, mut_assignments = next(load_mut_assignments(mutass))
    ssm_names = []
    for _, muts in mut_assignments.items():
      ssm_names += [m['name'] for m in muts['ssms']]
    ssm_names.sort(key = _ssm_key)

    idx_lookup = {name: i for (i, name) in enumerate(ssm_names)}
    return (ssm_names, idx_lookup)
