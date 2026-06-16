"use client";

import React, { useRef, useEffect, useState } from "react";

interface Node {
  id: string;
  label: string;
  type: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface Link {
  source: string;
  target: string;
  relation: string;
}

interface GraphViewerProps {
  data: {
    nodes: Node[];
    links: Link[];
  };
}

export default function GraphViewer({ data }: GraphViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
  
  // Graph state persisted across renders
  const graphStateRef = useRef<{
    nodes: Node[];
    links: Link[];
    zoom: number;
    panX: number;
    panY: number;
    draggedNode: Node | null;
  }>({
    nodes: [],
    links: [],
    zoom: 1,
    panX: 0,
    panY: 0,
    draggedNode: null,
  });

  // Track drag starting points
  const dragStartRef = useRef({ x: 0, y: 0, panX: 0, panY: 0, isPanning: false });

  // Node type color styling mapping (Black & White Theme / High Contrast Accent)
  const getNodeColor = (type: string) => {
    switch (type) {
      case "Company":
        return { fill: "#FFFFFF", stroke: "#000000", text: "#000000" };
      case "Product":
        return { fill: "#000000", stroke: "#FFFFFF", text: "#FFFFFF" };
      case "Technology":
        return { fill: "#1F1F1F", stroke: "#8C8C8C", text: "#E5E5E5" };
      case "Person":
        return { fill: "#E5E5E5", stroke: "#000000", text: "#000000" };
      case "Event":
        return { fill: "#8C8C8C", stroke: "#FFFFFF", text: "#FFFFFF" };
      default:
        return { fill: "#111111", stroke: "#404040", text: "#A3A3A3" };
    }
  };

  // Sync prop changes into ref state
  useEffect(() => {
    const state = graphStateRef.current;
    
    // Merge existing nodes to preserve coordinates during increments
    const existingMap = new Map<string, Node>();
    state.nodes.forEach(n => existingMap.set(n.id, n));
    
    const newNodes = data.nodes.map(n => {
      const existing = existingMap.get(n.id);
      if (existing) {
        return { ...n, x: existing.x, y: existing.y, vx: existing.vx, vy: existing.vy };
      }
      // Random starting coordinates near center
      const width = canvasRef.current?.width || 500;
      const height = canvasRef.current?.height || 400;
      return {
        ...n,
        x: width / 2 + (Math.random() - 0.5) * 100,
        y: height / 2 + (Math.random() - 0.5) * 100,
        vx: 0,
        vy: 0
      };
    });

    state.nodes = newNodes;
    state.links = data.links;
  }, [data]);

  // Main canvas drawing & physics loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;

    const resizeCanvas = () => {
      if (containerRef.current && canvas) {
        canvas.width = containerRef.current.clientWidth;
        canvas.height = containerRef.current.clientHeight;
      }
    };
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    // Physics constants
    const REPULSION = 400;
    const ATTRACTION = 0.04;
    const GRAVITY = 0.02;
    const FRICTION = 0.88;
    const REST_LENGTH = 90;
    const NODE_RADIUS = 18;

    const updateAndDraw = () => {
      const state = graphStateRef.current;
      const width = canvas.width;
      const height = canvas.height;
      const nodes = state.nodes;
      const links = state.links;

      // 1. Calculate physics forces
      // Repulsion between all nodes
      for (let i = 0; i < nodes.length; i++) {
        const n1 = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j];
          if (n1.x === undefined || n1.y === undefined || n2.x === undefined || n2.y === undefined) continue;
          
          let dx = n2.x - n1.x;
          let dy = n2.y - n1.y;
          if (dx === 0 && dy === 0) {
            dx = 0.1; // break symmetry
          }
          const dist = Math.sqrt(dx * dx + dy * dy);
          const force = -REPULSION / (dist * dist + 1);
          
          const fx = force * (dx / dist);
          const fy = force * (dy / dist);
          
          n1.vx = (n1.vx || 0) + fx;
          n1.vy = (n1.vy || 0) + fy;
          n2.vx = (n2.vx || 0) - fx;
          n2.vy = (n2.vy || 0) - fy;
        }
      }

      // Attraction along links
      links.forEach(link => {
        const sourceNode = nodes.find(n => n.id === link.source);
        const targetNode = nodes.find(n => n.id === link.target);
        
        if (sourceNode && targetNode && 
            sourceNode.x !== undefined && sourceNode.y !== undefined &&
            targetNode.x !== undefined && targetNode.y !== undefined) {
          const dx = targetNode.x - sourceNode.x;
          const dy = targetNode.y - sourceNode.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
          const force = ATTRACTION * (dist - REST_LENGTH);
          
          const fx = force * (dx / dist);
          const fy = force * (dy / dist);
          
          sourceNode.vx = (sourceNode.vx || 0) + fx;
          sourceNode.vy = (sourceNode.vy || 0) + fy;
          targetNode.vx = (targetNode.vx || 0) - fx;
          targetNode.vy = (targetNode.vy || 0) - fy;
        }
      });

      // Gravity pulling to center
      const cx = width / 2;
      const cy = height / 2;
      nodes.forEach(node => {
        if (node.x !== undefined && node.y !== undefined) {
          node.vx = (node.vx || 0) + (cx - node.x) * GRAVITY;
          node.vy = (node.vy || 0) + (cy - node.y) * GRAVITY;
        }
      });

      // Update velocities & coordinates
      nodes.forEach(node => {
        if (node === state.draggedNode) return; // ignore dragged node
        if (node.x !== undefined && node.y !== undefined) {
          node.vx = (node.vx || 0) * FRICTION;
          node.vy = (node.vy || 0) * FRICTION;
          node.x += node.vx;
          node.y += node.vy;
        }
      });

      // 2. Clear canvas & Render Background grid lines
      ctx.fillStyle = "#080808";
      ctx.fillRect(0, 0, width, height);
      
      // Grid lines helper
      ctx.strokeStyle = "#121212";
      ctx.lineWidth = 1;
      const gridSpacing = 40;
      
      // Draw grid offset by panning
      const startX = (state.panX % gridSpacing) - gridSpacing;
      const startY = (state.panY % gridSpacing) - gridSpacing;
      
      for (let x = startX; x < width; x += gridSpacing) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = startY; y < height; y += gridSpacing) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Apply zoom & pan translation matrix
      ctx.save();
      ctx.translate(state.panX, state.panY);
      ctx.scale(state.zoom, state.zoom);

      // 3. Render Links
      links.forEach(link => {
        const sourceNode = nodes.find(n => n.id === link.source);
        const targetNode = nodes.find(n => n.id === link.target);
        
        if (sourceNode && targetNode &&
            sourceNode.x !== undefined && sourceNode.y !== undefined &&
            targetNode.x !== undefined && targetNode.y !== undefined) {
          
          ctx.beginPath();
          ctx.moveTo(sourceNode.x, sourceNode.y);
          ctx.lineTo(targetNode.x, targetNode.y);
          ctx.strokeStyle = "#262626";
          ctx.lineWidth = 1.5;
          ctx.stroke();
          
          // Draw arrow pointer
          const angle = Math.atan2(targetNode.y - sourceNode.y, targetNode.x - sourceNode.x);
          const arrowLength = 7;
          // Position arrow slightly before node radius
          const ax = targetNode.x - (NODE_RADIUS + 2) * Math.cos(angle);
          const ay = targetNode.y - (NODE_RADIUS + 2) * Math.sin(angle);
          
          ctx.beginPath();
          ctx.moveTo(ax, ay);
          ctx.lineTo(ax - arrowLength * Math.cos(angle - Math.PI / 6), ay - arrowLength * Math.sin(angle - Math.PI / 6));
          ctx.lineTo(ax - arrowLength * Math.cos(angle + Math.PI / 6), ay - arrowLength * Math.sin(angle + Math.PI / 6));
          ctx.closePath();
          ctx.fillStyle = "#404040";
          ctx.fill();

          // Link relation text in middle
          const mx = (sourceNode.x + targetNode.x) / 2;
          const my = (sourceNode.y + targetNode.y) / 2;
          ctx.save();
          ctx.translate(mx, my);
          ctx.rotate(Math.abs(angle) < Math.PI / 2 ? angle : angle + Math.PI);
          ctx.fillStyle = "#525252";
          ctx.font = "8px monospace";
          ctx.textAlign = "center";
          ctx.fillText(link.relation, 0, -3);
          ctx.restore();
        }
      });

      // 4. Render Nodes
      nodes.forEach(node => {
        if (node.x === undefined || node.y === undefined) return;
        
        const style = getNodeColor(node.type);
        const isHovered = hoveredNode?.id === node.id;
        
        ctx.beginPath();
        ctx.arc(node.x, node.y, NODE_RADIUS + (isHovered ? 2 : 0), 0, 2 * Math.PI);
        ctx.fillStyle = style.fill;
        ctx.fill();
        ctx.strokeStyle = isHovered ? "#FFFFFF" : style.stroke;
        ctx.lineWidth = isHovered ? 2.5 : 1.5;
        ctx.stroke();

        // Optional shadow glow for hovered node
        if (isHovered) {
          ctx.shadowBlur = 10;
          ctx.shadowColor = "#FFFFFF";
        }

        // Draw label text
        ctx.fillStyle = style.text;
        ctx.font = "bold 9px monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        
        // Truncate label if too long
        let label = node.label;
        if (label.length > 7) {
          label = label.substring(0, 5) + "..";
        }
        ctx.fillText(label, node.x, node.y);
        ctx.shadowBlur = 0; // reset shadow

        // Render type tag above node on hover
        if (isHovered) {
          ctx.fillStyle = "#A3A3A3";
          ctx.font = "8px sans-serif";
          ctx.fillText(node.type, node.x, node.y - NODE_RADIUS - 8);
        }
      });

      ctx.restore();
      animationId = requestAnimationFrame(updateAndDraw);
    };

    animationId = requestAnimationFrame(updateAndDraw);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", resizeCanvas);
    };
  }, [hoveredNode]);

  // Handle zooming using wheel
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const state = graphStateRef.current;
    const zoomFactor = 1.05;
    if (e.deltaY < 0) {
      state.zoom = Math.min(3, state.zoom * zoomFactor);
    } else {
      state.zoom = Math.max(0.3, state.zoom / zoomFactor);
    }
  };

  // Convert canvas mouse coordinates to translated graph world coordinates
  const screenToWorld = (screenX: number, screenY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: screenX, y: screenY };
    const rect = canvas.getBoundingClientRect();
    const state = graphStateRef.current;
    const x = (screenX - rect.left - state.panX) / state.zoom;
    const y = (screenY - rect.top - state.panY) / state.zoom;
    return { x, y };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    const state = graphStateRef.current;
    const worldCoords = screenToWorld(e.clientX, e.clientY);
    
    // 1. Check if clicked on a node to drag
    let clickedNode: Node | null = null;
    const NODE_RADIUS = 18;
    
    for (let i = state.nodes.length - 1; i >= 0; i--) {
      const node = state.nodes[i];
      if (node.x !== undefined && node.y !== undefined) {
        const dx = node.x - worldCoords.x;
        const dy = node.y - worldCoords.y;
        if (Math.sqrt(dx * dx + dy * dy) <= NODE_RADIUS) {
          clickedNode = node;
          break;
        }
      }
    }

    if (clickedNode) {
      state.draggedNode = clickedNode;
    } else {
      // 2. Dragging empty space means panning
      dragStartRef.current = {
        x: e.clientX,
        y: e.clientY,
        panX: state.panX,
        panY: state.panY,
        isPanning: true
      };
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const state = graphStateRef.current;
    const worldCoords = screenToWorld(e.clientX, e.clientY);
    
    // 1. Node dragging
    if (state.draggedNode) {
      state.draggedNode.x = worldCoords.x;
      state.draggedNode.y = worldCoords.y;
      state.draggedNode.vx = 0;
      state.draggedNode.vy = 0;
      return;
    }

    // 2. World Panning
    if (dragStartRef.current.isPanning) {
      const dx = e.clientX - dragStartRef.current.x;
      const dy = e.clientY - dragStartRef.current.y;
      state.panX = dragStartRef.current.panX + dx;
      state.panY = dragStartRef.current.panY + dy;
      return;
    }

    // 3. Hover detection
    let hovered: Node | null = null;
    const NODE_RADIUS = 18;
    for (let i = state.nodes.length - 1; i >= 0; i--) {
      const node = state.nodes[i];
      if (node.x !== undefined && node.y !== undefined) {
        const dx = node.x - worldCoords.x;
        const dy = node.y - worldCoords.y;
        if (Math.sqrt(dx * dx + dy * dy) <= NODE_RADIUS) {
          hovered = node;
          break;
        }
      }
    }
    
    if (hoveredNode?.id !== hovered?.id) {
      setHoveredNode(hovered);
    }
  };

  const handleMouseUp = () => {
    const state = graphStateRef.current;
    state.draggedNode = null;
    dragStartRef.current.isPanning = false;
  };

  // Zoom controls helper
  const adjustZoom = (factor: number) => {
    const state = graphStateRef.current;
    state.zoom = Math.max(0.3, Math.min(3, state.zoom * factor));
  };

  const resetZoom = () => {
    const state = graphStateRef.current;
    state.zoom = 1;
    state.panX = 0;
    state.panY = 0;
  };

  return (
    <div ref={containerRef} className="relative w-full h-[360px] md:h-[450px] border border-neutral-900 bg-[#080808] select-none rounded">
      <canvas
        ref={canvasRef}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="block cursor-grab active:cursor-grabbing"
      />
      
      {/* Zoom / Reset controller UI */}
      <div className="absolute bottom-4 right-4 flex space-x-2 bg-[#0d0d0d] border border-neutral-900 rounded p-1.5 shadow-lg">
        <button
          onClick={() => adjustZoom(1.1)}
          className="w-7 h-7 flex items-center justify-center font-mono text-white hover:bg-neutral-900 rounded text-sm transition"
          title="Zoom In"
        >
          +
        </button>
        <button
          onClick={() => adjustZoom(0.9)}
          className="w-7 h-7 flex items-center justify-center font-mono text-white hover:bg-neutral-900 rounded text-sm transition"
          title="Zoom Out"
        >
          -
        </button>
        <button
          onClick={resetZoom}
          className="px-2 h-7 flex items-center justify-center font-mono text-white hover:bg-neutral-900 rounded text-xs transition"
          title="Reset Fit"
        >
          FIT
        </button>
      </div>

      {/* Legend Card */}
      <div className="absolute top-4 left-4 bg-[#0c0c0c]/85 backdrop-blur-md border border-neutral-900 p-3 rounded text-[10px] text-neutral-400 font-mono flex flex-col space-y-1.5 select-none pointer-events-none">
        <span className="text-white border-b border-neutral-900 pb-1 mb-1 block font-bold text-[9px] uppercase tracking-wide">LEGEND</span>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-white border border-black inline-block"></span>
          <span>Company</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-black border border-white inline-block"></span>
          <span>Product</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#1F1F1F] border border-[#8C8C8C] inline-block"></span>
          <span>Technology</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#E5E5E5] border border-black inline-block"></span>
          <span>Person</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#8C8C8C] border border-white inline-block"></span>
          <span>Event</span>
        </div>
      </div>
      
      {/* Node inspect tooltip */}
      {hoveredNode && (
        <div className="absolute bottom-4 left-4 bg-[#0d0d0d] border border-neutral-900 px-3 py-2 rounded text-[11px] font-mono text-neutral-300 max-w-[200px] shadow-xl">
          <div className="text-white font-bold">{hoveredNode.label}</div>
          <div className="text-[10px] text-neutral-500 mt-0.5">{hoveredNode.type}</div>
        </div>
      )}
    </div>
  );
}
