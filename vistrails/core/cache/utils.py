############################################################################
##
## Copyright (C) 2006-2009 University of Utah. All rights reserved.
##
## This file is part of VisTrails.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-license.php
##
## If you are unsure which license is appropriate for your use (for
## instance, you are interested in developing a commercial derivative
## of VisTrails), please contact us at vistrails@sci.utah.edu.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################
"""Helper functions for cache package."""

try:
    import hashlib
    sha_hash = hashlib.sha1
except ImportError:
    import sha
    sha_hash = sha.new

##############################################################################

def hash_list(lst, hasher_f, constant_hasher_map={}):
    hasher = sha_hash()
    hash_l = [hasher_f(el, constant_hasher_map) for el in lst]
    hash_l.sort()
    for hel in hash_l: hasher.update(hel)
    return hasher.digest()
