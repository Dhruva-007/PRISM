/**
 * CitySelector component for PRISM.
 *
 * Dropdown that allows switching between supported Indian cities.
 * Appears in the TopBar and affects all data operations.
 */

"use client";

import { MapPin, ChevronDown, Check } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCity } from "@/hooks/useCity";

export function CitySelector() {
  const { cities, selectedCity, selectCity } = useCity();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-border bg-background hover:bg-stone-50 transition-colors duration-150 outline-none">
        <MapPin className="w-3.5 h-3.5 text-accent" />
        <span className="text-xs font-medium text-foreground">
          {selectedCity?.display_name ?? "Select City"}
        </span>
        <ChevronDown className="w-3 h-3 text-muted-foreground" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {cities.map((city) => (
          <DropdownMenuItem
            key={city.city_id}
            onClick={() => selectCity(city.city_id)}
            className="cursor-pointer"
          >
            <div className="flex items-center justify-between w-full gap-2">
              <div className="flex flex-col">
                <span className="text-xs font-medium">
                  {city.display_name}
                </span>
                <span className="text-[10px] text-muted-foreground">
                  {city.state} · {city.district_count} districts · {city.construction_sites} sites
                </span>
              </div>
              {selectedCity?.city_id === city.city_id && (
                <Check className="w-3.5 h-3.5 text-accent flex-shrink-0" />
              )}
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}