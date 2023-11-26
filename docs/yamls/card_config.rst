Card YAML Config Files
======================

.. csv-table::
   :header: "Name", "C Data Type", "Description"

   "bool", "bool", "A true / false value"
   "int8", "int8_t", "8-bit signed integer"
   "int16", "int16_t", "16-bit signed integer"
   "int32", "int32_t", "32-bit signed integer"
   "int64", "int64_t", "64-bit signed integer"
   "uint8", "uint8_t", "8-bit unsigned integer"
   "uint16", "uint16_t", "16-bit unsigned integer"
   "uint32", "uint32_t", "32-bit unsigned integer"
   "uint64", "uint64_t", "64-bit unsigned integer"
   "float32", "float", "32-bit floating point number"
   "float64", "double", "64-bit (double-precision) floating point number"
   "visable_str", "char []", "An ASCII string"
   "octet_str", "uint8_t []", "An octet string"
   "domain", "void \*", "A null value that must be have callback function(s)"


.. autoclass:: oresat_configs.card_config.CardConfig()
   :members:

.. autoclass:: oresat_configs.card_config.IndexObject()
   :inherited-members:
   :members:

.. autoclass:: oresat_configs.card_config.SubindexObject()
   :inherited-members:
   :members:

.. autoclass:: oresat_configs.card_config.GenerateSubindex()
   :inherited-members:
   :members:

.. autoclass:: oresat_configs.card_config.Tpdo()
   :members:

.. autoclass:: oresat_configs.card_config.Rpdo()
   :members:
