import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  animate?: boolean;
}

export function Card({ children, className, hover = false, animate = true }: CardProps) {
  const Component = animate ? motion.div : 'div';
  
  return (
    <Component
      {...(animate && {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.3 },
      })}
      {...(hover && animate && {
        whileHover: { scale: 1.02 },
      })}
      className={cn(
        'bg-white rounded-xl shadow-lg border border-gray-100 p-6',
        'transition-all duration-300',
        hover && 'hover:shadow-xl cursor-pointer',
        className
      )}
    >
      {children}
    </Component>
  );
}
