from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections
### exporting step file trial
# SONATA utilities
from SONATA.utl.blade_utl import (
    array_pln_intersect,
    check_uniformity,
    interp_airfoil_position,
    interp_loads,
    make_loft
)

def export_step(shapes, filename):
    """
    Export shapes to STEP file.
    
    Parameters
    ----------
    shapes : list or TopoDS_Shape
        List of TopoDS_Shape objects or single shape to export
    filename : str
        Output STEP file path
        
    Returns
    -------
    None
    
    Raises
    ------
    RuntimeError
        If STEP file writing fails
    """
    from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCC.Core.IFSelect import IFSelect_RetDone
    
    step_writer = STEPControl_Writer()
    
    # Handle single shape or list of shapes
    if not isinstance(shapes, (list, tuple)):
        shapes = [shapes]
    
    # Transfer each shape to the STEP writer
    for shape in shapes:
        step_writer.Transfer(shape, STEPControl_AsIs)
    
    # Write to file
    status = step_writer.Write(filename)
    
    if status != IFSelect_RetDone:
        raise RuntimeError(f"Error writing STEP file: {filename}")
    
    print(f"STATUS:\t Successfully exported blade to {filename}")

def blade_export_step(blade_object , output_name="blade.step", method="continuous"):
    """
    Generate blade loft and export to STEP (no GUI).
    
    Parameters
    ----------
    output_name : str, optional
        Output filename for STEP export. Default is "blade.step"
    method : str, optional
        Lofting method: 'continuous' for single surface through all sections,
        or 'segmented' for multiple surfaces between consecutive pairs.
        Default is 'continuous'
    """

    
    print(f"STATUS:\t Generating blade loft for STEP export...")
    
    # Collect all airfoil wires
    wireframe = []
    for bm, afl in zip(blade_object.blade_matrix, blade_object.airfoils[:, 1]):
        wire, _ = afl.trsf_to_blfr(bm[1:4], bm[6], bm[4], bm[5])
        wireframe.append(wire)

    if method == "continuous":
        # Create single continuous loft through all sections
        loft_generator = BRepOffsetAPI_ThruSections(isSolid= True, ruled=True)  # (isSolid=False, ruled=True)
        
        for wire in wireframe:
            loft_generator.AddWire(wire)
        
        # loft_generator.CheckCompatibility(False)
        loft_generator.Build()
        
        if loft_generator.IsDone():
            blade_surface = loft_generator.Shape()
            export_step([blade_surface], output_name)
        else:
            raise RuntimeError("Continuous loft generation failed")
    
    elif method == "segmented":
        # Create separate lofts between consecutive pairs (original method)
        loft_shapes = []
        for i in range(len(wireframe) - 1):
            loft = make_loft(
                wireframe[i:i+2],
                ruled=True,
                tolerance=1e-6,
                continuity=1,
                check_compatibility=True
            )
            loft_shapes.append(loft)
        
        export_step(loft_shapes, output_name)
    
    else:
        raise ValueError(f"Unknown method: {method}. Use 'continuous' or 'segmented'")