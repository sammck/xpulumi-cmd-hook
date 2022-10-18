# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Wrapped pulumi CLI that delegates to """


from typing import Optional, Sequence, Tuple, List, MutableMapping, Mapping, Generator

import os
import sys
import importlib
import subprocess

def searchpath_parts_remove_dir(parts: List[str], dirname: str) -> List[str]:
  dirname = os.path.abspath(os.path.normpath(os.path.expanduser(dirname)))
  result = [ x for x in parts if x != dirname ]
  return result

def searchpath_split(searchpath: Optional[str]=None) -> List[str]:
  if searchpath is None:
    searchpath = os.environ['PATH']
  result = [ x for x in searchpath.split(os.pathsep) if x != '' ]
  return result

def searchpath_join(dirnames: List[str]) -> str:
  return os.pathsep.join(dirnames)

def searchpath_remove_dir(searchpath: Optional[str], dirname: str) -> str:
  return searchpath_join(searchpath_parts_remove_dir(searchpath_split(searchpath), dirname))

def get_git_root_dir(starting_dir: Optional[str]=None) -> Optional[str]:
  """Find the root directory of the current git project

  Args:
      starting_dir (str, optional): The subdir in which to begin the search.
                      If None, "." is used. Defaults to None.

  Returns:
      Optional[str]:  The absolute pathname of the top-level git project directory, or
                      None if starting_dir is not in a git project.
  """
  if starting_dir is None:
    starting_dir = '.'
  starting_dir = os.path.abspath(starting_dir)
  rel_root_dir: Optional[str] = None
  try:
    rel_root_dir = subprocess.check_output(
        ['git', '-C', starting_dir, 'rev-parse', '--show-cdup'],
        stderr=subprocess.DEVNULL,
      ).decode('utf-8').rstrip()
  except subprocess.CalledProcessError:
    pass
  result = None if rel_root_dir is None else os.path.abspath(os.path.join(starting_dir, rel_root_dir))
  return result

def _get_base_prefix() -> str:
  return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix

def _get_virtualenv() -> Optional[str]:
  return None if sys.prefix == _get_base_prefix() else sys.prefix

def deactivate_virtualenv(env: Optional[MutableMapping]=None):
  """Modifies env vars to deactivate any activated virtualenv.

     Works on the current os environment or a dict/MutableMapping.

  Args:
      env (Optional[MutableMapping], optional):
              The environment to modify. If None, modifies the current
              os.environ.  Defaults to None.
  """
  if env is None:
    env = os.environ
  if 'VIRTUAL_ENV' in env:
    venv = env['VIRTUAL_ENV']
    del env['VIRTUAL_ENV']
    if 'POETRY_ACTIVE' in env:
      del env['POETRY_ACTIVE']
    if 'PATH' in env:
      venv_bin = os.path.join(venv, 'bin')
      env['PATH'] = searchpath_remove_dir(env['PATH'], venv_bin)

def pathname_is_executable(pathname: str) -> bool:
  return os.path.isfile(pathname) and os.access(pathname, os.X_OK)

def find_commands_in_path(
      cmd: str,
      searchpath: Optional[str]=None,
      cwd: Optional[str]=None
    ) -> Generator[str, None, None]:
  if cwd is None:
    cwd = '.'
  cwd = os.path.abspath(os.path.expanduser(cwd))
  cmd = os.path.expanduser(cmd)
  if os.path.sep in cmd or (not os.path.altsep is None and os.path.altsep in cmd):
    fq_cmd = os.path.abspath(os.path.join(cwd, cmd))
    if pathname_is_executable(fq_cmd):
      yield fq_cmd
    return
  for path_dir in searchpath_split(searchpath):
    fq_cmd = os.path.abspath(os.path.join(cwd, os.path.expanduser(path_dir), cmd))
    if pathname_is_executable(fq_cmd):
      yield fq_cmd

def find_command_in_path(cmd: str, searchpath: Optional[str]=None, cwd: Optional[str]=None) -> Optional[str]:
  for fq_cmd in find_commands_in_path(cmd, searchpath=searchpath, cwd=cwd):
    return fq_cmd
  return None

def get_raw_pulumi() -> Tuple[Optional[str], Optional[str]]:
  pulumi_home: Optional[str] = os.environ.get('PULUMI_HOME', '')
  if pulumi_home == '':
    project_root_dir = get_git_root_dir()
    if not project_root_dir is None:
      project_pulumi_home = os.path.join(project_root_dir, '.local', '.pulumi')
      project_pulumi_prog = os.path.join(project_pulumi_home, 'bin', 'pulumi')
      if os.path.exists(project_pulumi_prog):
        return project_pulumi_prog, project_pulumi_home
    virtualenv_dir = _get_virtualenv()
    if not virtualenv_dir is None:
      project_root_dir = get_git_root_dir(starting_dir=virtualenv_dir)
      if not project_root_dir is None:
        project_pulumi_home = os.path.join(project_root_dir, '.local', '.pulumi')
        project_pulumi_prog = os.path.join(project_pulumi_home, 'bin', 'pulumi')
        if os.path.exists(project_pulumi_prog):
          return project_pulumi_prog, project_pulumi_home
    novenv = dict(os.environ)
    deactivate_virtualenv(novenv)
    path_pulumi_prog = find_command_in_path('pulumi', searchpath=novenv['PATH'])
    if not path_pulumi_prog is None:
      path_pulumi_home = os.path.dirname(os.path.dirname(path_pulumi_prog))
      return path_pulumi_prog, path_pulumi_home
  else:
    pulumi_prog = os.path.join(pulumi_home, 'bin', 'pulumi')
    if os.path.exists(pulumi_prog):
      return pulumi_prog, pulumi_home
  return None, None

def run_raw_pulumi(arglist: List[str], env: Optional[Mapping[str, str]]=None) -> int:
  pulumi_prog, pulumi_home = get_raw_pulumi()
  if pulumi_prog is None:
    print('pulumi: command not found', file=sys.stderr)
    return 127
  if env is None:
    env = os.environ
  env = dict(env)
  env['PULUMI_HOME'] = pulumi_home
  result = subprocess.call([ pulumi_prog ] + arglist, env=env)
  return result

def run(argv: Optional[Sequence[str]]=None, env: Optional[Mapping[str, str]]=None) -> int:
  try:
    xpulumi_cli_wrapper = importlib.import_module('xpulumi.pulumi_cli.wrapper')
  except ModuleNotFoundError:
    return run_raw_pulumi(argv, env=env)
  return xpulumi_cli_wrapper.run_pulumi_wrapper(argv)
