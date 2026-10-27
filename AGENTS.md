# quantdata

Follow STYLE_GUIDE.md for Python style and numerical correctness. This is a standalone data package, not an experiment framework. Locations are raw and processed only. Keep generated outputs outside Git. Preserve the quantdata import namespace until explicitly migrating it. Tests are offline and must never download fixtures implicitly. Do not use a GPU without gpuctl allocation. Shared temporary files for this consolidation belong under /tmp/quant_data/.
